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

from sqlalchemy_bind_manager._repository import SortDirection
from sqlalchemy_bind_manager._repository.common import (
    MODEL,
    PRIMARY_KEY,
)
from sqlalchemy_bind_manager.repository import (
    CursorPaginatedResult,
    CursorReference,
    PaginatedResult,
)


@runtime_checkable
class SQLAlchemyAsyncRepositoryInterface(Protocol[MODEL]):
    async def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted
        """
        ...

    async def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        """Persist many models in a single database get_session.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :return: The model instances after being persisted
        """
        ...

    async def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFound: No model has been found using the primary key
        """
        ...

    async def get_many(self, identifiers: Iterable[PRIMARY_KEY]) -> List[MODEL]:
        """Get a list of models by primary keys.

        :param identifiers: A list of primary keys
        :type identifiers: List
        :return: A list of models
        :rtype: List
        """
        ...

    async def delete(self, instance: MODEL) -> None:
        """Deletes a model.

        :param instance: The model instance
        """
        ...

    async def delete_many(self, instances: Iterable[MODEL]) -> None:
        """Deletes a collection of models in a single transaction.

        :param instances: The model instances
        """
        ...

    async def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        """Find models using filters.

        E.g.
        find(search_params={"name":"John"})
            finds all models with name = John

        find(order_by=["name"])
            finds all models ordered by `name` column

        find(order_by=[("name", SortDirection.DESC)])
            finds all models with reversed order by `name` column

        :param search_params: A mapping containing equality filters
        :type search_params: Mapping
        :param order_by:
        :type order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]]
        :return: A collection of models
        :rtype: List
        """
        ...

    async def paginated_find(
        self,
        items_per_page: int,
        page: int = 1,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> PaginatedResult[MODEL]:
        """Find models using filters and limit/offset pagination. Returned results
        do include pagination metadata.

        E.g.
        paginated_find(search_params={"name":"John"})
            finds all models with name = John

        paginated_find(50, search_params={"name":"John"})
            finds first 50 models with name = John

        paginated_find(50, 3, search_params={"name":"John"})
            finds 50 models with name = John, skipping 2 pages (100)

        paginated_find(order_by=["name"])
            finds all models ordered by `name` column

        paginated_find(order_by=[("name", SortDirection.DESC)])
            finds all models with reversed order by `name` column

        :param items_per_page: Number of models to retrieve
        :type items_per_page: int
        :param page: Page to retrieve
        :type page: int
        :param search_params: A mapping containing equality filters
        :type search_params: Mapping
        :param order_by:
        :type order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]]
        :return: A collection of models
        :rtype: List
        """
        ...

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
        cursor_paginated_find(search_params={"name":"John"})
            finds all models with name = John

        cursor_paginated_find(50, search_params={"name":"John"})
            finds first 50 models with name = John

        cursor_paginated_find(50, CursorReference(column="id", value=123))
            finds first 50 models after the one with "id" 123

        cursor_paginated_find(50, CursorReference(column="id", value=123), True)
            finds last 50 models before the one with "id" 123

        :param items_per_page: Number of models to retrieve
        :type items_per_page: int
        :param cursor_reference: A cursor reference containing ordering column
            and threshold value
        :type cursor_reference: Union[CursorReference, None]
        :param is_before_cursor: If True it will return items before the cursor,
            otherwise items after
        :type is_before_cursor: bool
        :param search_params: A mapping containing equality filters
        :type search_params: Mapping
        :return: A collection of models
        :rtype: List
        """
        ...


@runtime_checkable
class SQLAlchemyRepositoryInterface(Protocol[MODEL]):
    def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted
        """
        ...

    def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        """Persist many models in a single database get_session.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :return: The model instances after being persisted
        """
        ...

    def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFound: No model has been found using the primary key
        """
        ...

    def get_many(self, identifiers: Iterable[PRIMARY_KEY]) -> List[MODEL]:
        """Get a list of models by primary keys.

        :param identifiers: A list of primary keys
        :type identifiers: List
        :return: A list of models
        :rtype: List
        """
        ...

    def delete(self, instance: MODEL) -> None:
        """Deletes a model.

        :param instance: The model instance
        """
        ...

    async def delete_many(self, instances: Iterable[MODEL]) -> None:
        """Deletes a collection of models in a single transaction.

        :param instances: The model instances
        """
        ...

    def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        """Find models using filters.

        E.g.
        find(search_params={"name":"John"})
            finds all models with name = John

        find(order_by=["name"])
            finds all models ordered by `name` column

        find(order_by=[("name", SortDirection.DESC)])
            finds all models with reversed order by `name` column

        :param search_params: A mapping containing equality filters
        :type search_params: Mapping
        :param order_by:
        :type order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]]
        :return: A collection of models
        :rtype: List
        """
        ...

    def paginated_find(
        self,
        items_per_page: int,
        page: int = 1,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> PaginatedResult[MODEL]:
        """Find models using filters and limit/offset pagination. Returned results
        do include pagination metadata.

        E.g.
        paginated_find(search_params={"name":"John"})
            finds all models with name = John

        paginated_find(50, search_params={"name":"John"})
            finds first 50 models with name = John

        paginated_find(50, 3, search_params={"name":"John"})
            finds 50 models with name = John, skipping 2 pages (100)

        paginated_find(order_by=["name"])
            finds all models ordered by `name` column

        paginated_find(order_by=[("name", SortDirection.DESC)])
            finds all models with reversed order by `name` column

        :param items_per_page: Number of models to retrieve
        :type items_per_page: int
        :param page: Page to retrieve
        :type page: int
        :param search_params: A mapping containing equality filters
        :type search_params: Mapping
        :param order_by:
        :type order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]]
        :return: A collection of models
        :rtype: List
        """
        ...

    def cursor_paginated_find(
        self,
        items_per_page: int,
        cursor_reference: Union[CursorReference, None] = None,
        is_before_cursor: bool = False,
        search_params: Union[None, Mapping[str, Any]] = None,
    ) -> CursorPaginatedResult[MODEL]:
        """Find models using filters and cursor based pagination. Returned results
        do include pagination metadata.

        E.g.
        cursor_paginated_find(search_params={"name":"John"})
            finds all models with name = John

        cursor_paginated_find(50, search_params={"name":"John"})
            finds first 50 models with name = John

        cursor_paginated_find(50, CursorReference(column="id", value=123))
            finds first 50 models after the one with "id" 123

        cursor_paginated_find(50, CursorReference(column="id", value=123), True)
            finds last 50 models before the one with "id" 123

        :param items_per_page: Number of models to retrieve
        :type items_per_page: int
        :param cursor_reference: A cursor reference containing ordering column
            and threshold value
        :type cursor_reference: Union[CursorReference, None]
        :param is_before_cursor: If True it will return items before the cursor,
            otherwise items after
        :type is_before_cursor: bool
        :param search_params: A mapping containing equality filters
        :type search_params: Mapping
        :return: A collection of models
        :rtype: List
        """
        ...
