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

from enum import Enum
from functools import partial
from typing import Callable, Generic, List, TypeVar, Union

from pydantic import BaseModel, StrictInt, StrictStr
from sqlalchemy import asc, desc

MODEL = TypeVar("MODEL")
PRIMARY_KEY = Union[str, int, tuple, dict]


class PageInfo(BaseModel):
    page: int
    items_per_page: int
    total_pages: int
    total_items: int
    has_next_page: bool
    has_previous_page: bool


class PaginatedResult(BaseModel, Generic[MODEL]):
    items: List[MODEL]
    page_info: PageInfo


class CursorReference(BaseModel):
    column: str
    value: Union[StrictStr, StrictInt]


class CursorPageInfo(BaseModel):
    items_per_page: int
    total_items: int
    has_next_page: bool = False
    has_previous_page: bool = False
    start_cursor: Union[CursorReference, None] = None
    end_cursor: Union[CursorReference, None] = None


class CursorPaginatedResult(BaseModel, Generic[MODEL]):
    items: List[MODEL]
    page_info: CursorPageInfo


class SortDirection(Enum):
    ASC: Callable = partial(asc)
    DESC: Callable = partial(desc)
