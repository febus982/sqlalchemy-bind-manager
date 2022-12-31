from abc import ABC
from enum import Enum
from functools import partial
from typing import Union, TypeVar, Generic, Type, Iterable, Tuple

from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, object_mapper, Mapper, class_mapper
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.sql import Select

from ._bind_manager import SQLAlchemyBindManager, DEFAULT_BIND_NAME
from .exceptions import (
    ModelNotFound,
    UnmappedProperty,
    InvalidModel,
)


MODEL = TypeVar("MODEL")
PRIMARY_KEY = Union[str, int, tuple, dict]


class SortDirection(Enum):
    ASC = partial(asc)
    DESC = partial(desc)


class SQLAlchemyRepository(Generic[MODEL], ABC):
    _sa_manager: SQLAlchemyBindManager
    _bind_name: str
    _model: Type[MODEL]

    def __init__(
        self, sa_manager: SQLAlchemyBindManager, bind_name: str = DEFAULT_BIND_NAME
    ) -> None:
        """

        :param sa_manager: A configured instance of SQLAlchemyBindManager
        :type sa_manager: SQLAlchemyBindManager
        :param bind_name: The name of the bind as defined in the SQLAlchemyConfig. defaults to "default"
        """
        super().__init__()
        self._sa_manager = sa_manager
        self._bind_name = bind_name

    def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted (e.g. with primary key populated)
        """
        with self._sa_manager.get_session() as session:  # type: ignore
            session.add(instance)
            self._commit(session)
        return instance

    def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        """Persist many models in a single database transaction.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :return: The model instances after being persisted (e.g. with primary keys populated)
        """
        with self._sa_manager.get_session() as session:  # type: ignore
            session.add_all(instances)
            self._commit(session)
        return instances

    def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFound: No model has been found using the primary key
        """
        # TODO: implement get_many()
        with self._sa_manager.get_session() as session:  # type: ignore
            model = session.get(self._model, identifier)
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    def delete(self, entity: Union[MODEL, PRIMARY_KEY]) -> None:
        """Deletes a model.

        :param entity: The model instance or the primary key
        :type entity: Union[MODEL, PRIMARY_KEY]
        """
        # TODO: delete without loading the model
        obj = entity if self._is_mapped_object(entity) else self.get(entity)  # type: ignore
        with self._sa_manager.get_session() as session:  # type: ignore
            session.delete(obj)
            self._commit(session)

    def find(
        self,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
        **search_params,
    ) -> Iterable[MODEL]:
        """Find models using filters

        E.g.
        find(name="John") finds all models with name = John

        :param order_by:
        :param search_params: Any keyword argument to be used as equality filter
        :return: A collection of models
        :rtype: Iterable
        """
        stmt = select(self._model)  # type: ignore
        stmt = self._filter_select(stmt, **search_params)

        if order_by is not None:
            stmt = self._filter_order_by(stmt, order_by)

        with self._sa_manager.get_session() as session:  # type: ignore
            result = session.execute(stmt)
            for model_obj in result.scalars():
                yield model_obj

    def _commit(self, session: Union[Session, AsyncSession]) -> None:
        """Commits the session and handles rollback on errors.

        :param session: The session object.
        :type session: Union[Session, AsyncSession]
        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            session.commit()
        except:
            session.rollback()
            raise

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

    def _filter_select(self, stmt: Select, **search_params) -> Select:
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
