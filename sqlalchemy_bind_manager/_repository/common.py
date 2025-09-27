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

from typing import Generic, List, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, StrictInt, StrictStr

MODEL = TypeVar("MODEL")
PRIMARY_KEY = Union[str, int, tuple, dict, UUID]


class PageInfo(BaseModel):
    """
    Paginated query metadata.

    :param page: The current page number
    :type page: int
    :param items_per_page: The maximum number of items in a page.
    :type items_per_page: int
    :param total_pages: The number of available pages.
    :type total_pages: int
    :param total_items: The total items in all the pages.
    :type total_items: int
    :param has_next_page: True if there is a next page.
    :type has_next_page: bool
    :param has_previous_page: True if there is a previous page.
    :type has_previous_page: bool
    """

    page: int
    items_per_page: int
    total_pages: int
    total_items: int
    has_next_page: bool
    has_previous_page: bool


class PaginatedResult(BaseModel, Generic[MODEL]):
    """
    The result of a paginated query.

    :param items: The models returned by the query
    :type items: List[MODEL]
    :param page_info: The pagination metadata
    :type page_info: PageInfo
    """

    items: List[MODEL]
    page_info: PageInfo


class CursorReference(BaseModel):
    column: str
    value: Union[StrictStr, StrictInt, UUID]


class CursorPageInfo(BaseModel):
    """
    Cursor-paginated query metadata.

    :param items_per_page: The maximum number of items in a page.
    :type items_per_page: int
    :param total_items: The total items in all the pages.
    :type total_items: int
    :param has_next_page: True if there is a next page.
    :type has_next_page: bool
    :param has_previous_page: True if there is a previous page.
    :type has_previous_page: bool
    :param start_cursor: The cursor pointing to the first item in the page,
    if at least one item is returned.
    :type start_cursor: Union[CursorReference, None]
    :param end_cursor: The cursor pointing to the last item in the page,
    if at least one item is returned.
    :type end_cursor: Union[CursorReference, None]
    """

    items_per_page: int
    total_items: int
    has_next_page: bool = False
    has_previous_page: bool = False
    start_cursor: Union[CursorReference, None] = None
    end_cursor: Union[CursorReference, None] = None


class CursorPaginatedResult(BaseModel, Generic[MODEL]):
    """
    The result of a cursor paginated query.

    :param items: The models returned by the query
    :type items: List[MODEL]
    :param page_info: The pagination metadata
    :type page_info: CursorPageInfo
    """

    items: List[MODEL]
    page_info: CursorPageInfo
