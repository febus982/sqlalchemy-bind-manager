from abc import ABC
from contextlib import contextmanager
from typing import Union, Generic, Iterable, Tuple, List, Iterator, Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import scoped_session

from .._bind_manager import SQLAlchemyBind
from .._unit_of_work import SQLAlchemyUnitOfWork
from ..exceptions import ModelNotFound
from .common import MODEL, PRIMARY_KEY, SortDirection, BaseRepository


class SQLAlchemyRepository(Generic[MODEL], BaseRepository[MODEL], ABC):
    _UOW: SQLAlchemyUnitOfWork

    def __init__(self, bind: SQLAlchemyBind) -> None:
        """
        :param bind: A configured instance of SQLAlchemyBind
        :type bind: SQLAlchemyBind
        """
        super().__init__()
        self._UOW = SQLAlchemyUnitOfWork(bind)

    @contextmanager
    def _get_session(
        self, session: Union[scoped_session, None] = None, commit: bool = True
    ) -> Iterator[scoped_session]:
        if not session:
            with self._UOW.get_session(commit) as _session:
                yield _session
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

    def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
        session: Union[scoped_session, None] = None,
    ) -> List[MODEL]:
        """Find models using filters

        E.g.
        find(name="John") finds all models with name = John

        :param order_by:
        :param search_params: A dictionary containing equality filters
        :param session: Optional session with externally-managed lifecycle
        :return: A collection of models
        :rtype: List
        """
        stmt = select(self._model)  # type: ignore
        if search_params:
            stmt = self._filter_select(stmt, search_params)

        if order_by is not None:
            stmt = self._filter_order_by(stmt, order_by)

        with self._get_session(session) as session:
            result = session.execute(stmt)
            return [x for x in result.scalars()]
