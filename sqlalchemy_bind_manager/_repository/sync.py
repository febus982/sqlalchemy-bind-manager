from abc import ABC
from contextlib import contextmanager
from typing import Union, Generic, Iterable, Tuple, List, Iterator, Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from .._bind_manager import SQLAlchemyBind
from .._transaction_handler import SessionHandler
from ..exceptions import ModelNotFound, InvalidConfig
from .common import MODEL, PRIMARY_KEY, SortDirection, BaseRepository


class SQLAlchemyRepository(Generic[MODEL], BaseRepository[MODEL], ABC):
    _session_handler: SessionHandler
    _external_session: Union[Session, None]

    def __init__(
        self,
        bind: Union[SQLAlchemyBind, None] = None,
        session: Union[Session, None] = None,
    ) -> None:
        """
        :param bind: A configured instance of SQLAlchemyBind
        :type bind: SQLAlchemyBind
        :param session: An externally managed session
        :type session: Session
        """
        super().__init__()
        if not (bool(bind) ^ bool(session)):
            raise InvalidConfig("Either `bind` or `session` have to be used, not both")
        self._external_session = session
        if bind:
            self._session_handler = SessionHandler(bind)

    @contextmanager
    def _get_session(self, commit: bool = True) -> Iterator[Session]:
        if not self._external_session:
            with self._session_handler.get_session(not commit) as _session:
                yield _session
        else:
            yield self._external_session

    def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted (e.g. with primary key populated)
        """
        with self._get_session() as session:
            session.add(instance)
        return instance

    def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        """Persist many models in a single database get_session.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :return: The model instances after being persisted (e.g. with primary keys populated)
        """
        with self._get_session() as session:
            session.add_all(instances)
        return instances

    def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFound: No model has been found using the primary key
        """
        # TODO: implement get_many()
        with self._get_session(commit=False) as session:
            model = session.get(self._model, identifier)
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    def delete(self, entity: Union[MODEL, PRIMARY_KEY]) -> None:
        """Deletes a model.

        :param entity: The model instance or the primary key
        :type entity: Union[MODEL, PRIMARY_KEY]
        """
        # TODO: delete without loading the model
        obj = entity if self._is_mapped_object(entity) else self.get(entity)  # type: ignore
        with self._get_session() as session:
            session.delete(obj)

    def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        """Find models using filters

        E.g.
        find(name="John") finds all models with name = John

        :param order_by:
        :param search_params: A dictionary containing equality filters
        :return: A collection of models
        :rtype: List
        """
        stmt = select(self._model)
        if search_params:
            stmt = self._filter_select(stmt, search_params)

        if order_by is not None:
            stmt = self._filter_order_by(stmt, order_by)

        with self._get_session() as session:
            result = session.execute(stmt)
            return [x for x in result.scalars()]
