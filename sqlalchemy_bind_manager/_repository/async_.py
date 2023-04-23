from abc import ABC
from contextlib import asynccontextmanager
from typing import (
    Union,
    Generic,
    Tuple,
    Iterable,
    List,
    AsyncIterator,
    Any,
    Mapping,
    Type,
)

from sqlalchemy.ext.asyncio import AsyncSession

from .._bind_manager import SQLAlchemyAsyncBind
from .._transaction_handler import AsyncSessionHandler
from ..exceptions import ModelNotFound, InvalidConfig
from .common import MODEL, PRIMARY_KEY, SortDirection, BaseRepository, PaginatedResult


class SQLAlchemyAsyncRepository(Generic[MODEL], BaseRepository[MODEL], ABC):
    _session_handler: AsyncSessionHandler
    _external_session: Union[AsyncSession, None]

    def __init__(
        self,
        bind: Union[SQLAlchemyAsyncBind, None] = None,
        session: Union[AsyncSession, None] = None,
        model_class: Union[Type[MODEL], None] = None,
    ) -> None:
        """
        :param bind: A configured instance of SQLAlchemyAsyncBind
        :type bind: Union[SQLAlchemyAsyncBind, None]
        :param session: An externally managed session
        :type session: Union[AsyncSession, None]
        :param model_class: A mapped SQLAlchemy model
        :type model_class: Union[Type[MODEL], None]
        """
        super().__init__(model_class=model_class)
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
        :param limit: Number of models to retrieve
        :type limit: int
        :param offset: Number of models to skip
        :type offset: int
        :return: A collection of models
        :rtype: List
        """
        stmt = self._find_query(search_params, order_by)

        async with self._get_session() as session:
            result = await session.execute(stmt)
            return [x for x in result.scalars()]

    async def paginated_find(
        self,
        per_page: int,
        page: int,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> PaginatedResult[MODEL]:
        """Find models using filters and pagination

        E.g.
        find(name="John") finds all models with name = John

        :param per_page: Number of models to retrieve
        :type per_page: int
        :param page: Page to retrieve
        :type page: int
        :param search_params: A dictionary containing equality filters
        :param order_by:
        :return: A collection of models
        :rtype: List
        """

        find_stmt = self._find_query(search_params, order_by)
        paginated_stmt = self._paginate_query(find_stmt, page, per_page)

        async with self._get_session() as session:
            total_items_count = (
                await session.execute(self._count_query(find_stmt))
            ).scalar() or 0
            result_items = [
                x for x in (await session.execute(paginated_stmt)).scalars()
            ]

            return self._build_paginated_result(
                result_items=result_items,
                total_items_count=total_items_count,
                page=page,
                per_page=per_page,
            )
