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

#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#
from typing import (
    Any,
    Iterable,
    List,
    Literal,
    Mapping,
    Protocol,
    Tuple,
    Union,
)

from .common import (
    MODEL,
    PRIMARY_KEY,
    CursorPaginatedResult,
    CursorReference,
    PaginatedResult,
)


class SQLAlchemyAsyncRepositoryInterface(Protocol[MODEL]):
    async def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFoundError: No model has been found using the primary key
        """
        ...

    async def get_many(self, identifiers: Iterable[PRIMARY_KEY]) -> List[MODEL]:
        """Get a list of models by primary keys.

        :param identifiers: A list of primary keys
        :return: A list of models
        """
        ...

    async def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted
        """
        ...

    async def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        """Persist many models in a single database get_session.

        :param instances: A list of mapped objects to be persisted
        :return: The model instances after being persisted
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
        ...

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
        ...


class SQLAlchemyRepositoryInterface(Protocol[MODEL]):
    def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFoundError: No model has been found using the primary key
        """
        ...

    def get_many(self, identifiers: Iterable[PRIMARY_KEY]) -> List[MODEL]:
        """Get a list of models by primary keys.

        :param identifiers: A list of primary keys
        :return: A list of models
        """
        ...

    def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted
        """
        ...

    def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        """Persist many models in a single database get_session.

        :param instances: A list of mapped objects to be persisted
        :return: The model instances after being persisted
        """
        ...

    def delete(self, instance: MODEL) -> None:
        """Deletes a model.

        :param instance: The model instance
        """
        ...

    def delete_many(self, instances: Iterable[MODEL]) -> None:
        """Deletes a collection of models in a single transaction.

        :param instances: The model instances
        """
        ...

    def find(
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
        ...

    def paginated_find(
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
        ...
