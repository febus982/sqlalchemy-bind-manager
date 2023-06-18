from abc import ABC
from enum import Enum
from functools import partial
from typing import (
    Any,
    Generic,
    Iterable,
    Mapping,
    Tuple,
    Type,
    Union,
)

from sqlalchemy import asc, desc, func, inspect, select
from sqlalchemy.orm import Mapper, aliased, class_mapper, lazyload
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.sql import Select

from sqlalchemy_bind_manager.exceptions import InvalidModel, UnmappedProperty

from .common import (
    MODEL,
    CursorReference,
)


class SortDirection(Enum):
    ASC = partial(asc)
    DESC = partial(desc)


class BaseRepository(Generic[MODEL], ABC):
    _max_query_limit: int = 50
    _model: Type[MODEL]

    def __init__(self, model_class: Union[Type[MODEL], None] = None) -> None:
        if getattr(self, "_model", None) is None and model_class is not None:
            self._model = model_class

        if getattr(self, "_model", None) is None or not self._is_mapped_class(
            self._model
        ):
            raise InvalidModel(
                "You need to supply a valid model class"
                " either in the `model_class` parameter"
                " or in the `_model` class property."
            )

    def _is_mapped_class(self, class_: Type[MODEL]) -> bool:
        """Checks if the class is mapped in SQLAlchemy.

        :param class_: the model class
        :return: True if the Type is mapped, False otherwise
        :rtype: bool
        """
        try:
            class_mapper(class_)
            return True
        except UnmappedClassError:
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
                f"Property `{property_name}` is not mapped"
                f" in the ORM for model `{self._model}`"
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
        `_filter_order_by(stmt, ['name'])`
            adds a `ORDER BY name` statement

        `_filter_order_by(stmt, [('name', SortDirection.ASC)])`
            adds a `ORDER BY name ASC` statement

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
            query.options(lazyload("*")).subquery()  # type: ignore
        )

    def _paginate_query_by_page(
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

        _limit = self._sanitised_query_limit(per_page)
        stmt = stmt.limit(_limit)

        return stmt

    def _cursor_paginated_query(
        self,
        stmt: Select,
        cursor_reference: Union[CursorReference, None],
        is_end_cursor: bool = False,
        per_page: int = _max_query_limit,
    ) -> Select:
        """Build the query offset and limit clauses from submitted parameters.

        :param stmt: a Select statement
        :type stmt: Select
        :param before: Identifier of the last node to skip
        :type before: Union[int, str]
        :param after: Identifier of the last node to skip
        :type after: Union[int, str]
        :param per_page: Number of models to retrieve
        :type per_page: int
        :return: The filtered query
        """

        forward_limit = self._sanitised_query_limit(per_page) + 1

        if not cursor_reference:
            return stmt.limit(forward_limit).order_by(  # type: ignore
                asc(self._model_pk())
            )

        # TODO: Use window functions
        if not is_end_cursor:
            previous_query = stmt.where(
                getattr(self._model, cursor_reference.column) <= cursor_reference.value
            )
            previous_query = (
                self._filter_order_by(
                    previous_query, [(cursor_reference.column, SortDirection.DESC)]
                )
                .limit(1)
                .subquery("previous")  # type: ignore
            )

            page_query = stmt.where(
                getattr(self._model, cursor_reference.column) > cursor_reference.value
            )
            page_query = (
                self._filter_order_by(
                    page_query, [(cursor_reference.column, SortDirection.ASC)]
                )
                .limit(forward_limit)
                .subquery("page")  # type: ignore
            )
        else:
            previous_query = stmt.where(
                getattr(self._model, cursor_reference.column) >= cursor_reference.value
            )
            previous_query = (
                self._filter_order_by(
                    previous_query, [(cursor_reference.column, SortDirection.ASC)]
                )
                .limit(1)
                .subquery("previous")  # type: ignore
            )

            page_query = stmt.where(
                getattr(self._model, cursor_reference.column) < cursor_reference.value
            )
            page_query = (
                self._filter_order_by(
                    page_query, [(cursor_reference.column, SortDirection.DESC)]
                )
                .limit(forward_limit)
                .subquery("page")  # type: ignore
            )

        query = select(
            aliased(
                self._model,
                select(previous_query)
                .union(select(page_query))
                .order_by(cursor_reference.column)
                .subquery(),  # type: ignore
            )
        )

        return query

    def _sanitised_query_limit(self, limit):
        return max(min(limit, self._max_query_limit), 0)

    def _model_pk(self) -> str:
        primary_keys = inspect(self._model).primary_key  # type: ignore
        if len(primary_keys) > 1:
            raise NotImplementedError("Composite primary keys are not supported.")

        return primary_keys[0].name