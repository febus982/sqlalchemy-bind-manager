from typing import Generic, List, TypeVar, Union

from pydantic import BaseModel
from pydantic.generics import GenericModel

MODEL = TypeVar("MODEL")
PRIMARY_KEY = Union[str, int, tuple, dict]


class PageInfo(BaseModel):
    page: int
    items_per_page: int
    total_pages: int
    total_items: int
    has_next_page: bool
    has_previous_page: bool


class PaginatedResult(GenericModel, Generic[MODEL]):
    items: List[MODEL]
    page_info: PageInfo


class CursorPageInfo(BaseModel):
    items_per_page: int
    total_items: int
    has_next_page: bool = False
    has_previous_page: bool = False
    start_cursor: Union[str, None] = None
    end_cursor: Union[str, None] = None


class CursorPaginatedResult(GenericModel, Generic[MODEL]):
    items: List[MODEL]
    page_info: CursorPageInfo


class Cursor(BaseModel):
    column: str
    value: str
