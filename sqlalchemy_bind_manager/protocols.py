from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    Protocol,
    Tuple,
    Union,
    runtime_checkable,
)

from sqlalchemy_bind_manager._repository.common import (
    MODEL,
    PRIMARY_KEY,
    Cursor,
    CursorPaginatedResult,
    PaginatedResult,
    SortDirection,
)


@runtime_checkable
class SQLAlchemyAsyncRepositoryInterface(Protocol[MODEL]):
    async def save(self, instance: MODEL) -> MODEL:
        ...

    async def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        ...

    async def get(self, identifier: PRIMARY_KEY) -> MODEL:
        ...

    async def delete(self, entity: Union[MODEL, PRIMARY_KEY]) -> None:
        ...

    async def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        ...

    async def paginated_find(
        self,
        items_per_page: int,
        page: int,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> PaginatedResult[MODEL]:
        ...

    async def cursor_paginated_find(
        self,
        items_per_page: int,
        reference_cursor: Union[Cursor, str, None] = None,
        is_end_cursor: bool = False,
        search_params: Union[None, Mapping[str, Any]] = None,
    ) -> CursorPaginatedResult[MODEL]:
        ...


@runtime_checkable
class SQLAlchemyRepositoryInterface(Protocol[MODEL]):
    def save(self, instance: MODEL) -> MODEL:
        ...

    def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        ...

    def get(self, identifier: PRIMARY_KEY) -> MODEL:
        ...

    def delete(self, entity: Union[MODEL, PRIMARY_KEY]) -> None:
        ...

    def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        ...

    def paginated_find(
        self,
        items_per_page: int,
        page: int,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> PaginatedResult[MODEL]:
        ...

    def cursor_paginated_find(
        self,
        items_per_page: int,
        reference_cursor: Union[Cursor, str, None] = None,
        is_end_cursor: bool = False,
        search_params: Union[None, Mapping[str, Any]] = None,
    ) -> CursorPaginatedResult[MODEL]:
        ...
