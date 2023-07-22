from abc import ABC
from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncIterator,
    Generic,
    Iterable,
    List,
    Mapping,
    Tuple,
    Type,
    Union,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .._bind_manager import SQLAlchemyAsyncBind
from .._session_handler import AsyncSessionHandler
from ..exceptions import InvalidConfig, ModelNotFound
from .base_repository import (
    BaseRepository,
)
from .common import (
    MODEL,
    PRIMARY_KEY,
    CursorPaginatedResult,
    CursorReference,
    PaginatedResult,
    SortDirection,
)
from .result_presenters import CursorPaginatedResultPresenter, PaginatedResultPresenter


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
        self._fail_if_invalid_models([instance])
        async with self._get_session() as session:
            session.add(instance)
        return instance

    async def save_many(
        self,
        instances: Iterable[MODEL],
    ) -> Iterable[MODEL]:
        self._fail_if_invalid_models(instances)
        async with self._get_session() as session:
            session.add_all(instances)
        return instances

    async def get(self, identifier: PRIMARY_KEY) -> MODEL:
        async with self._get_session(commit=False) as session:
            model = await session.get(self._model, identifier)
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    async def get_many(self, identifiers: Iterable[PRIMARY_KEY]) -> List[MODEL]:
        stmt = select(self._model).where(
            getattr(self._model, self._model_pk()).in_(identifiers)
        )

        async with self._get_session(commit=False) as session:
            return [x for x in (await session.execute(stmt)).scalars()]

    async def delete(self, instance: MODEL) -> None:
        self._fail_if_invalid_models([instance])
        async with self._get_session() as session:
            await session.delete(instance)

    async def delete_many(self, instances: Iterable[MODEL]) -> None:
        self._fail_if_invalid_models(instances)
        async with self._get_session() as session:
            for instance in instances:
                await session.delete(instance)

    async def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        stmt = self._find_query(search_params, order_by)

        async with self._get_session() as session:
            result = await session.execute(stmt)
            return [x for x in result.scalars()]

    async def paginated_find(
        self,
        items_per_page: int,
        page: int = 1,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> PaginatedResult[MODEL]:
        find_stmt = self._find_query(search_params, order_by)
        paginated_stmt = self._paginate_query_by_page(find_stmt, page, items_per_page)

        async with self._get_session() as session:
            total_items_count = (
                await session.execute(self._count_query(find_stmt))
            ).scalar() or 0
            result_items = [
                x for x in (await session.execute(paginated_stmt)).scalars()
            ]

            return PaginatedResultPresenter.build_result(
                result_items=result_items,
                total_items_count=total_items_count,
                page=page,
                items_per_page=self._sanitised_query_limit(items_per_page),
            )

    async def cursor_paginated_find(
        self,
        items_per_page: int,
        cursor_reference: Union[CursorReference, None] = None,
        is_before_cursor: bool = False,
        search_params: Union[None, Mapping[str, Any]] = None,
    ) -> CursorPaginatedResult[MODEL]:
        find_stmt = self._find_query(search_params)
        paginated_stmt = self._cursor_paginated_query(
            find_stmt,
            cursor_reference=cursor_reference,
            is_before_cursor=is_before_cursor,
            items_per_page=items_per_page,
        )

        async with self._get_session() as session:
            total_items_count = (
                await session.execute(self._count_query(find_stmt))
            ).scalar() or 0
            result_items = [
                x for x in (await session.execute(paginated_stmt)).scalars()
            ] or []

            return CursorPaginatedResultPresenter.build_result(
                result_items=result_items,
                total_items_count=total_items_count,
                items_per_page=self._sanitised_query_limit(items_per_page),
                cursor_reference=cursor_reference,
                is_before_cursor=is_before_cursor,
            )
