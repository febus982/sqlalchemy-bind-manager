#  Copyright (c) 2024 Federico Busetti <729029+febus982@users.noreply.github.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncIterator,
    Generic,
    Iterable,
    List,
    Literal,
    Mapping,
    Tuple,
    Type,
    Union,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .._bind_manager import SQLAlchemyAsyncBind
from .._session_handler import AsyncSessionHandler
from ..exceptions import InvalidConfigError, ModelNotFoundError
from .base_repository import (
    BaseRepository,
)
from .common import (
    MODEL,
    PRIMARY_KEY,
    CursorPaginatedResult,
    CursorReference,
    PaginatedResult,
)
from .result_presenters import CursorPaginatedResultPresenter, PaginatedResultPresenter


class SQLAlchemyAsyncRepository(
    Generic[MODEL],
    BaseRepository[MODEL],
):
    _session_handler: AsyncSessionHandler
    _external_session: Union[AsyncSession, None]

    def __init__(
        self,
        bind: Union[SQLAlchemyAsyncBind, None] = None,
        session: Union[AsyncSession, None] = None,
        model_class: Union[Type[MODEL], None] = None,
    ) -> None:
        super().__init__(model_class=model_class)
        if not (bool(bind) ^ bool(session)):
            raise InvalidConfigError(
                "Either `bind` or `session` have to be used, not both"
            )
        self._external_session = session
        if bind:
            self._session_handler = AsyncSessionHandler(bind)

    async def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFoundError: No model has been found using the primary key
        """
        async with self._get_session(commit=False) as session:
            model = await session.get(self._model, identifier)
        if model is None:
            raise ModelNotFoundError("No rows found for provided primary key.")
        return model

    async def get_many(self, identifiers: Iterable[PRIMARY_KEY]) -> List[MODEL]:
        """Get a list of models by primary keys.

        :param identifiers: A list of primary keys
        :return: A list of models
        """
        stmt = select(self._model).where(
            getattr(self._model, self._model_pk()).in_(identifiers)
        )

        async with self._get_session(commit=False) as session:
            return [x for x in (await session.execute(stmt)).scalars()]

    async def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted
        """
        self._fail_if_invalid_models([instance])
        async with self._get_session() as session:
            session.add(instance)
        return instance

    async def save_many(
        self,
        instances: Iterable[MODEL],
    ) -> Iterable[MODEL]:
        """Persist many models in a single database get_session.

        :param instances: A list of mapped objects to be persisted
        :return: The model instances after being persisted
        """
        self._fail_if_invalid_models(instances)
        async with self._get_session() as session:
            session.add_all(instances)
        return instances

    async def delete(self, instance: MODEL) -> None:
        """Deletes a model.

        :param instance: The model instance
        """
        self._fail_if_invalid_models([instance])
        async with self._get_session() as session:
            await session.delete(instance)

    async def delete_many(self, instances: Iterable[MODEL]) -> None:
        """Deletes a collection of models in a single transaction.

        :param instances: The model instances
        """
        self._fail_if_invalid_models(instances)
        async with self._get_session() as session:
            for instance in instances:
                await session.delete(instance)

    async def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[
            None,
            Iterable[Union[str, Tuple[str, Literal["asc", "desc"]]]],
        ] = None,
    ) -> List[MODEL]:
        """Find models using filters.

        E.g.

            # find all models with name = John
            find(search_params={"name":"John"})

            # find all models ordered by `name` column
            find(order_by=["name"])

            # find all models with reversed order by `name` column
            find(order_by=[("name", "desc")])

        :param search_params: A mapping containing equality filters
        :param order_by:
        :return: A collection of models
        """
        stmt = self._find_query(search_params, order_by)

        async with self._get_session() as session:
            result = await session.execute(stmt)
            return [x for x in result.scalars()]

    async def paginated_find(
        self,
        items_per_page: int,
        page: int = 1,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[
            None,
            Iterable[Union[str, Tuple[str, Literal["asc", "desc"]]]],
        ] = None,
    ) -> PaginatedResult[MODEL]:
        """Find models using filters and limit/offset pagination. Returned results
        do include pagination metadata.

        E.g.

            # find all models with name = John
            paginated_find(search_params={"name":"John"})

            # find first 50 models with name = John
            paginated_find(50, search_params={"name":"John"})

            # find 50 models with name = John, skipping 2 pages (100)
            paginated_find(50, 3, search_params={"name":"John"})

            # find all models ordered by `name` column
            paginated_find(order_by=["name"])

            # find all models with reversed order by `name` column
            paginated_find(order_by=[("name", "desc")])

        :param items_per_page: Number of models to retrieve
        :param page: Page to retrieve
        :param search_params: A mapping containing equality filters
        :param order_by:
        :return: A collection of models
        """
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
        """Find models using filters and cursor based pagination. Returned results
        do include pagination metadata.

        E.g.

            # finds all models with name = John
            cursor_paginated_find(search_params={"name":"John"})

            # finds first 50 models with name = John
            cursor_paginated_find(50, search_params={"name":"John"})

            # finds first 50 models after the one with "id" 123
            cursor_paginated_find(50, CursorReference(column="id", value=123))

            # finds last 50 models before the one with "id" 123
            cursor_paginated_find(50, CursorReference(column="id", value=123), True)

        :param items_per_page: Number of models to retrieve
        :param cursor_reference: A cursor reference containing ordering column
            and threshold value
        :param is_before_cursor: If True it will return items before the cursor,
            otherwise items after
        :param search_params: A mapping containing equality filters
        :return: A collection of models
        """
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

    @asynccontextmanager
    async def _get_session(self, commit: bool = True) -> AsyncIterator[AsyncSession]:
        if not self._external_session:
            async with self._session_handler.get_session(not commit) as _session:
                yield _session
        else:
            yield self._external_session
