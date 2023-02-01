from abc import ABC
from enum import Enum
from functools import partial
from typing import TypeVar, Union, Generic, Type, Tuple, Iterable, Any, Mapping

from sqlalchemy import asc, desc
from sqlalchemy.orm import object_mapper, class_mapper, Mapper
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.sql import Select

from sqlalchemy_bind_manager.exceptions import InvalidModel, UnmappedProperty

MODEL = TypeVar("MODEL")
PRIMARY_KEY = Union[str, int, tuple, dict]


class SortDirection(Enum):
    ASC = partial(asc)
    DESC = partial(desc)


class BaseRepository(Generic[MODEL], ABC):
    _model: Type[MODEL]

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
        if property_name not in m.column_attrs:  # type: ignore
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
        # TODO: Add support for offset/limit
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
