from abc import ABC
from enum import Enum
from functools import partial
from math import ceil
from typing import (
    TypeVar,
    Union,
    Generic,
    Type,
    Tuple,
    Iterable,
    Any,
    Mapping,
    List,
    Collection,
)

from pydantic.generics import GenericModel
from sqlalchemy import asc, desc, select, func
from sqlalchemy.orm import object_mapper, class_mapper, Mapper, lazyload
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.sql import Select

from sqlalchemy_bind_manager.exceptions import InvalidModel, UnmappedProperty

MODEL = TypeVar("MODEL")
PRIMARY_KEY = Union[str, int, tuple, dict]


class SortDirection(Enum):
    ASC = partial(asc)
    DESC = partial(desc)


class PaginatedResult(GenericModel, Generic[MODEL]):
    items: List[MODEL]
    page: int
    per_page: int
    total_pages: int
    total_items: int


class BaseRepository(Generic[MODEL], ABC):
    _max_query_limit: int = 50
    _model: Type[MODEL]

    def __init__(self, model_class: Union[Type[MODEL], None] = None) -> None:
        if getattr(self, "_model", None) is None and model_class is not None:
            self._model = model_class

        if getattr(self, "_model", None) is None or not self._is_mapped_object(
            self._model()
        ):
            raise InvalidModel(
                "You need to supply a valid model class either in the `model_class` parameter"
                " or in the `_model` class property."
            )

    def _is_mapped_object(self, obj: object) -> bool:
        """Checks if the object is handled by the repository and is mapped in SQLAlchemy.

        :param obj: a mapped object instance
        :return: True if the object is mapped and matches self._model type, False if it's not a mapped object
        :rtype: bool
        :raises InvalidModel: when the object is mapped but doesn't match self._model type
        """
        # TODO: This is probably redundant, we could do these checks once in __init__
        try:
            object_mapper(obj)
            if isinstance(obj, self._model):
                return True
            raise InvalidModel(
                f"This repository can handle only `{self._model}` models. `{type(obj)}` has been passed."
            )
        except UnmappedInstanceError:
            return False

    def _validate_mapped_property(self, property_name: str) -> None:
        """Checks if a property is mapped in the model class.

        :param property_name: The name of the property to be evaluated.
        :type property_name: str
        :raises UnmappedProperty: When the property is not mapped.
        """
        m: Mapper = class_mapper(self._model)
        if property_name not in m.column_attrs:
            raise UnmappedProperty(
                f"Property `{property_name}` is not mapped in the ORM for model `{self._model}`"
            )

    def _filter_select(self, stmt: Select, search_params: Mapping[str, Any]) -> Select:
        """Build the query filtering clauses from submitted parameters.

        E.g.
        _filter_select(stmt, name="John") adds a `WHERE name = John` statement

        :param stmt: a Select statement
        :type stmt: Select
        :param search_params: Any keyword argument to be used as equality filter
        :return: The filtered query
        """
        # TODO: Add support for relationship eager load
        for k, v in search_params.items():
            """
            This acts as a TypeGuard but using TypeGuard typing would break
            compatibility with python < 3.10, for the moment we prefer to ignore
            typing issues here
            """
            self._validate_mapped_property(k)
            stmt = stmt.where(getattr(self._model, k) == v)
        return stmt

    def _filter_order_by(
        self, stmt: Select, order_by: Iterable[Union[str, Tuple[str, SortDirection]]]
    ) -> Select:
        """Build the query ordering clauses from submitted parameters.

        E.g.
        _filter_order_by(stmt, ['name']) adds a `ORDER BY name` statement
        _filter_order_by(stmt, [('name', SortDirection.ASC)]) adds a `ORDER BY name ASC` statement

        :param stmt: a Select statement
        :type stmt: Select
        :param order_by: a list of columns, or tuples (column, direction)
        :return: The filtered query
        """
        for value in order_by:
            if isinstance(value, str):
                self._validate_mapped_property(value)
                stmt = stmt.order_by(getattr(self._model, value))
            else:
                self._validate_mapped_property(value[0])
                stmt = stmt.order_by(value[1].value(getattr(self._model, value[0])))

        return stmt

    def _find_query(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> Select:
        stmt = select(self._model)

        if search_params:
            stmt = self._filter_select(stmt, search_params)
        if order_by is not None:
            stmt = self._filter_order_by(stmt, order_by)

        return stmt

    def _count_query(
        self,
        query: Select,
    ) -> Select:
        return select(func.count()).select_from(
            query.options(lazyload("*")).order_by(None).subquery()  # type: ignore
        )

    def _paginate_query(
        self,
        stmt: Select,
        page: int,
        per_page: int,
    ) -> Select:
        """Build the query offset and limit clauses from submitted parameters.

        :param stmt: a Select statement
        :type stmt: Select
        :param page: Number of models to skip
        :type page: int
        :param per_page: Number of models to retrieve
        :type per_page: int
        :return: The filtered query
        """

        _offset = max((page - 1) * per_page, 0)
        if _offset > 0:
            stmt = stmt.offset(_offset)

        _limit = max(min(per_page, self._max_query_limit), 0)
        stmt = stmt.limit(_limit)

        return stmt

    def _build_paginated_result(
        self,
        result_items: Collection[MODEL],
        total_items_count: int,
        page: int,
        per_page: int,
    ) -> PaginatedResult:

        _per_page = max(min(per_page, self._max_query_limit), 0)
        total_pages = (
            0
            if total_items_count == 0 or total_items_count is None
            else ceil(total_items_count / _per_page)
        )
        _page = 0 if len(result_items) == 0 else min(page, total_pages)

        return PaginatedResult(
            items=result_items,
            page=_page,
            per_page=_per_page,
            total_items=total_items_count,
            total_pages=total_pages,
        )
