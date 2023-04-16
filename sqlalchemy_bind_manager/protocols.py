from typing import (
    Union,
    Mapping,
    Any,
    Iterable,
    Tuple,
    List,
    Protocol,
    runtime_checkable,
)

from sqlalchemy_bind_manager._repository.common import PRIMARY_KEY, MODEL, SortDirection


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
        limit: Union[None, int] = None,
        offset: Union[None, int] = None,
    ) -> List[MODEL]:
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
        limit: Union[None, int] = None,
        offset: Union[None, int] = None,
    ) -> List[MODEL]:
        ...
