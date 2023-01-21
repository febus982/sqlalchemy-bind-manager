from enum import Enum
from functools import partial
from typing import TypeVar, Union

from sqlalchemy import asc, desc


MODEL = TypeVar("MODEL")
PRIMARY_KEY = Union[str, int, tuple, dict]


class SortDirection(Enum):
    ASC = partial(asc)
    DESC = partial(desc)
