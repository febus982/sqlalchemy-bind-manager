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
