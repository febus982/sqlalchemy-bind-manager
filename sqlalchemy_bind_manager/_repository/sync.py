from abc import ABC
from contextlib import contextmanager
from typing import Union, Generic, Iterable, Tuple, List, Iterator
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session

from .._bind_manager import SQLAlchemyBindManager, DEFAULT_BIND_NAME, SQLAlchemyBind
from ..exceptions import (
    ModelNotFound,
    UnsupportedBind,
)
from .common import MODEL, PRIMARY_KEY, SortDirection, BaseRepository


class SQLAlchemySyncRepository(Generic[MODEL], BaseRepository[MODEL], ABC):
    Session: scoped_session

    def __init__(
        self, sa_manager: SQLAlchemyBindManager, bind_name: str = DEFAULT_BIND_NAME
    ) -> None:
        """

        :param sa_manager: A configured instance of SQLAlchemyBindManager
        :type sa_manager: SQLAlchemyBindManager
        :param bind_name: The name of the bind as defined in the SQLAlchemyConfig. defaults to "default"
        """
        bind = sa_manager.get_bind(bind_name)
        if not isinstance(bind, SQLAlchemyBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyBind")
        super().__init__()
        u = str(uuid4())
        self.Session = scoped_session(bind.session_class, scopefunc=lambda: str(u))

    def __del__(self):
        # If we fail to initialise the repository we might have no session attribute
        if not getattr(self, "Session", None):
            return

        self.Session.remove()

    @contextmanager
    def _get_session(
        self, session: Union[scoped_session, None] = None, commit: bool = True
    ) -> Iterator[scoped_session]:
        if not session:
            with self.Session() as _session:
                yield _session
                if commit:
                    self._commit(_session)
        else:
            yield session

    def save(
        self, instance: MODEL, session: Union[scoped_session, None] = None
    ) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :param session: Optional session with externally-managed lifecycle
        :return: The model instance after being persisted (e.g. with primary key populated)
        """
        with self._get_session(session) as session:  # type: ignore
            session.add(instance)
            self._commit(session)
        return instance

    def save_many(
        self, instances: Iterable[MODEL], session: Union[scoped_session, None] = None
    ) -> Iterable[MODEL]:
        """Persist many models in a single database transaction.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :param session: Optional session with externally-managed lifecycle
        :return: The model instances after being persisted (e.g. with primary keys populated)
        """
        with self._get_session(session) as session:  # type: ignore
            session.add_all(instances)
            self._commit(session)
        return instances

    def get(
        self, identifier: PRIMARY_KEY, session: Union[scoped_session, None] = None
    ) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :param session: Optional session with externally-managed lifecycle
        :return: A model instance
        :raises ModelNotFound: No model has been found using the primary key
        """
        # TODO: implement get_many()
        with self._get_session(session, commit=False) as session:
            model = session.get(self._model, identifier)  # type: ignore
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    def delete(
        self,
        entity: Union[MODEL, PRIMARY_KEY],
        session: Union[scoped_session, None] = None,
    ) -> None:
        """Deletes a model.

        :param entity: The model instance or the primary key
        :type entity: Union[MODEL, PRIMARY_KEY]
        :param session: Optional session with externally-managed lifecycle
        """
        # TODO: delete without loading the model
        obj = entity if self._is_mapped_object(entity) else self.get(entity)  # type: ignore
        with self._get_session(session) as session:
            session.delete(obj)
            self._commit(session)

    def find(
        self,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
        session: Union[scoped_session, None] = None,
        **search_params,
    ) -> List[MODEL]:
        """Find models using filters

        E.g.
        find(name="John") finds all models with name = John

        :param order_by:
        :param search_params: Any keyword argument to be used as equality filter
        :param session: Optional session with externally-managed lifecycle
        :return: A collection of models
        :rtype: List
        """
        stmt = select(self._model)  # type: ignore
        stmt = self._filter_select(stmt, **search_params)

        if order_by is not None:
            stmt = self._filter_order_by(stmt, order_by)

        with self._get_session(session) as session:
            result = session.execute(stmt)
            return [x for x in result.scalars()]

    def _commit(self, session: scoped_session) -> None:
        """Commits the session and handles rollback on errors.

        :param session: The session object.
        :type session: Session
        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            session.commit()
        except:
            session.rollback()
            raise
