from abc import ABC
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Union, Generic, Tuple, Iterable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_scoped_session

from .._bind_manager import SQLAlchemyBindManager, DEFAULT_BIND_NAME
from .._unit_of_work import SAAsyncUnitOfWork
from ..exceptions import ModelNotFound
from .common import MODEL, PRIMARY_KEY, SortDirection, BaseRepository


class SQLAlchemyAsyncRepository(Generic[MODEL], BaseRepository[MODEL], ABC):
    _UOW: SAAsyncUnitOfWork

    def __init__(
        self, sa_manager: SQLAlchemyBindManager, bind_name: str = DEFAULT_BIND_NAME
    ) -> None:
        """

        :param sa_manager: A configured instance of SQLAlchemyBindManager
        :type sa_manager: SQLAlchemyBindManager
        :param bind_name: The name of the bind as defined in the SQLAlchemyConfig. defaults to "default"
        """
        super().__init__()
        self._UOW = SAAsyncUnitOfWork(sa_manager.get_bind(bind_name))

    @asynccontextmanager
    async def _get_session(
        self, session: Union[async_scoped_session, None] = None, commit: bool = True
    ) -> AsyncIterator[async_scoped_session]:
        if not session:
            async with self._UOW.get_session(commit) as _session:
                yield _session
        else:
            yield session

    async def save(
        self, instance: MODEL, session: Union[async_scoped_session, None] = None
    ) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :param session: Optional session with externally-managed lifecycle
        :return: The model instance after being persisted (e.g. with primary key populated)
        """
        async with self._get_session(session) as session:  # type: ignore
            session.add(instance)
        return instance

    async def save_many(
        self,
        instances: Iterable[MODEL],
        session: Union[async_scoped_session, None] = None,
    ) -> Iterable[MODEL]:
        """Persist many models in a single database transaction.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :param session: Optional session with externally-managed lifecycle
        :return: The model instances after being persisted (e.g. with primary keys populated)
        """
        async with self._get_session(session) as session:  # type: ignore
            session.add_all(instances)
        return instances

    async def get(
        self, identifier: PRIMARY_KEY, session: Union[async_scoped_session, None] = None
    ) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :param session: Optional session with externally-managed lifecycle
        :raises ModelNotFound: No model has been found using the primary key
        """
        # TODO: implement get_many()
        async with self._get_session(session, commit=False) as session:
            model = await session.get(self._model, identifier)  # type: ignore
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    async def delete(
        self,
        entity: Union[MODEL, PRIMARY_KEY],
        session: Union[async_scoped_session, None] = None,
    ) -> None:
        """Deletes a model.

        :param entity: The model instance or the primary key
        :type entity: Union[MODEL, PRIMARY_KEY]
        :param session: Optional session with externally-managed lifecycle
        """
        # TODO: delete without loading the model
        obj = entity if self._is_mapped_object(entity) else await self.get(entity)  # type: ignore
        async with self._get_session(session) as session:  # type: ignore
            await session.delete(obj)

    async def find(
        self,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
        session: Union[async_scoped_session, None] = None,
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

        async with self._get_session(session) as session:  # type: ignore
            result = await session.execute(stmt)
            return [x for x in result.scalars()]
