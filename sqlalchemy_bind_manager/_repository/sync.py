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

from contextlib import contextmanager
from typing import (
    Any,
    Generic,
    Iterable,
    Iterator,
    List,
    Mapping,
    Tuple,
    Type,
    Union,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from .._bind_manager import SQLAlchemyBind
from .._session_handler import SessionHandler
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
    SortDirection,
)
from .result_presenters import CursorPaginatedResultPresenter, PaginatedResultPresenter


class SQLAlchemyRepository(Generic[MODEL], BaseRepository[MODEL]):
    _session_handler: SessionHandler
    _external_session: Union[Session, None]

    def __init__(
        self,
        bind: Union[SQLAlchemyBind, None] = None,
        session: Union[Session, None] = None,
        model_class: Union[Type[MODEL], None] = None,
    ) -> None:
        super().__init__(model_class=model_class)
        if not (bool(bind) ^ bool(session)):
            raise InvalidConfigError(
                "Either `bind` or `session` have to be used, not both"
            )
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
        self._fail_if_invalid_models([instance])
        with self._get_session() as session:
            session.add(instance)
        return instance

    def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        self._fail_if_invalid_models(instances)
        with self._get_session() as session:
            session.add_all(instances)
        return instances

    def get(self, identifier: PRIMARY_KEY) -> MODEL:
        with self._get_session(commit=False) as session:
            model = session.get(self._model, identifier)
        if model is None:
            raise ModelNotFoundError("No rows found for provided primary key.")
        return model

    def get_many(self, identifiers: Iterable[PRIMARY_KEY]) -> List[MODEL]:
        stmt = select(self._model).where(
            getattr(self._model, self._model_pk()).in_(identifiers)
        )

        with self._get_session(commit=False) as session:
            return [x for x in session.execute(stmt).scalars()]

    def delete(self, instance: MODEL) -> None:
        self._fail_if_invalid_models([instance])
        with self._get_session() as session:
            session.delete(instance)

    def delete_many(self, instances: Iterable[MODEL]) -> None:
        self._fail_if_invalid_models(instances)
        with self._get_session() as session:
            for model in instances:
                session.delete(model)

    def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        stmt = self._find_query(search_params, order_by)

        with self._get_session() as session:
            result = session.execute(stmt)
            return [x for x in result.scalars()]

    def paginated_find(
        self,
        items_per_page: int,
        page: int = 1,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> PaginatedResult[MODEL]:
        find_stmt = self._find_query(search_params, order_by)
        paginated_stmt = self._paginate_query_by_page(find_stmt, page, items_per_page)

        with self._get_session() as session:
            total_items_count = (
                session.execute(self._count_query(find_stmt)).scalar() or 0
            )
            result_items = [x for x in session.execute(paginated_stmt).scalars()]

            return PaginatedResultPresenter.build_result(
                result_items=result_items,
                total_items_count=total_items_count,
                page=page,
                items_per_page=self._sanitised_query_limit(items_per_page),
            )

    def cursor_paginated_find(
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

        with self._get_session() as session:
            total_items_count = (
                session.execute(self._count_query(find_stmt)).scalar() or 0
            )
            result_items = [x for x in session.execute(paginated_stmt).scalars()]

            return CursorPaginatedResultPresenter.build_result(
                result_items=result_items,
                total_items_count=total_items_count,
                items_per_page=self._sanitised_query_limit(items_per_page),
                cursor_reference=cursor_reference,
                is_before_cursor=is_before_cursor,
            )
