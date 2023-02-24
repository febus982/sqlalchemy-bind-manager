from abc import ABC
from contextlib import asynccontextmanager
from typing import Union, Generic, Tuple, Iterable, List, AsyncIterator, Any, Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .._bind_manager import SQLAlchemyAsyncBind
from .._transaction_handler import AsyncSessionHandler
from ..exceptions import ModelNotFound, InvalidConfig
from .common import MODEL, PRIMARY_KEY, SortDirection, BaseRepository


class SQLAlchemyAsyncRepository(Generic[MODEL], BaseRepository[MODEL], ABC):
    _session_handler: AsyncSessionHandler
    _external_session: Union[AsyncSession, None]

    def __init__(
        self,
        bind: Union[SQLAlchemyAsyncBind, None] = None,
        session: Union[AsyncSession, None] = None,
    ) -> None:
        """
        :param bind: A configured instance of SQLAlchemyAsyncBind
        :type bind: SQLAlchemyAsyncBind
        :param session: An externally managed session
        :type session: AsyncSession
        """
        super().__init__()
        if not (bool(bind) ^ bool(session)):
            raise InvalidConfig("Either `bind` or `session` have to be used, not both")
        self._external_session = session
        if bind:
            self._session_handler = AsyncSessionHandler(bind)

    @asynccontextmanager
    async def _get_session(self, commit: bool = True) -> AsyncIterator[AsyncSession]:
        if not self._external_session:
            async with self._session_handler.get_session(not commit) as _session:
                yield _session
        else:
            yield self._external_session

    async def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted (e.g. with primary key populated)
        """
        async with self._get_session() as session:
            session.add(instance)
        return instance

    async def save_many(
        self,
        instances: Iterable[MODEL],
    ) -> Iterable[MODEL]:
        """Persist many models in a single database get_session.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :return: The model instances after being persisted (e.g. with primary keys populated)
        """
        async with self._get_session() as session:
            session.add_all(instances)
        return instances

    async def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFound: No model has been found using the primary key
        """
        # TODO: implement get_many()
        async with self._get_session(commit=False) as session:
            model = await session.get(self._model, identifier)
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    async def delete(
        self,
        entity: Union[MODEL, PRIMARY_KEY],
    ) -> None:
        """Deletes a model.

        :param entity: The model instance or the primary key
        :type entity: Union[MODEL, PRIMARY_KEY]
        """
        # TODO: delete without loading the model
        obj = entity if self._is_mapped_object(entity) else await self.get(entity)  # type: ignore
        async with self._get_session() as session:
            await session.delete(obj)

    async def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        """Find models using filters

        E.g.
        find(search_params={"name": "John"}) finds all models with name = John

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

        async with self._get_session() as session:
            result = await session.execute(stmt)
            return [x for x in result.scalars()]
