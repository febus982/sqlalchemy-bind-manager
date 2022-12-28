from abc import ABC
from typing import Dict, Union, TypeVar, Generic, Type, Iterable, TypeGuard

from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session, object_mapper, Mapper, class_mapper
from sqlalchemy.orm.decl_api import registry
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.sql import Select

from sqlalchemy_bind_manager.exceptions import (
    NotInitializedBind,
    UnsupportedBind,
    InvalidConfig,
    ModelNotFound, UnmappedProperty, InvalidModel,
)


class SQLAlchemyBindConfig(BaseModel):
    engine_async: bool = False
    engine_options: Union[Dict, None]
    engine_url: str
    session_options: Union[Dict, None]


class SQLAlchemyBind(BaseModel):
    bind_async: bool
    engine: Union[Engine, AsyncEngine]
    model_declarative_base: type
    registry_mapper: registry
    session_class: sessionmaker

    class Config:
        arbitrary_types_allowed = True


SQLAlchemyConfig = Union[Dict[str, SQLAlchemyBindConfig], SQLAlchemyBindConfig]
MODEL = TypeVar("MODEL")
PRIMARY_KEY = Union[str, int, tuple, dict]
DEFAULT_BIND_NAME = "default"


class SQLAlchemyBindManager:
    __binds: Dict[str, SQLAlchemyBind]

    def __init__(self, config: SQLAlchemyConfig) -> None:
        self.__binds = {}
        if isinstance(config, dict):
            for name, conf in config.items():
                self.__init_bind(name, conf)
        else:
            self.__init_bind(DEFAULT_BIND_NAME, config)

    def __init_bind(self, name: str, config: SQLAlchemyBindConfig):
        if not isinstance(config, SQLAlchemyBindConfig):
            raise InvalidConfig(
                f"Config for bind `{name}` is not a SQLAlchemyBindConfig object"
            )

        engine_options: dict = config.engine_options or {}
        engine_options.setdefault("echo", False)
        engine_options.setdefault("future", True)

        session_options: dict = config.session_options or {}

        engine: Union[Engine, AsyncEngine]
        if config.engine_async:
            engine = create_async_engine(config.engine_url, **engine_options)
        else:
            engine = create_engine(config.engine_url, **engine_options)

        registry_mapper = registry()
        self.__binds[name] = SQLAlchemyBind(
            engine=engine,
            registry_mapper=registry_mapper,
            session_class=sessionmaker(
                bind=engine,
                class_=AsyncSession if config.engine_async else Session,
                **session_options,
            ),
            model_declarative_base=registry_mapper.generate_base(),
            bind_async=config.engine_async,
        )

    def get_binds(self) -> Dict[str, SQLAlchemyBind]:
        return self.__binds

    def get_bind_mappers_metadata(self) -> Dict[str, MetaData]:
        """
        Returns the mappers metadata in a format that can be used
        in Alembic configuration

        :returns: mappers metadata
        :rtype: dict
        """
        return {k: b.registry_mapper.metadata for k, b in self.__binds.items()}

    def get_bind(self, bind_name: str = DEFAULT_BIND_NAME) -> SQLAlchemyBind:
        try:
            return self.__binds[bind_name]
        except KeyError as err:
            raise NotInitializedBind(f"Bind not initialized")

    def get_session(self, bind: str = DEFAULT_BIND_NAME) -> Session:
        _bind = self.get_bind(bind)
        if not _bind.bind_async:
            return _bind.session_class()
        else:
            raise UnsupportedBind(
                "Requested bind is asynchronous. Use `get_async_session`"
            )

    def get_async_session(self, bind: str = DEFAULT_BIND_NAME) -> AsyncSession:
        _bind = self.get_bind(bind)
        if _bind.bind_async:
            return _bind.session_class()
        else:
            raise UnsupportedBind("Requested bind is synchronous. Use `get_session`")

    def get_mapper(self, bind: str = DEFAULT_BIND_NAME) -> registry:
        return self.get_bind(bind).registry_mapper


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

    def find(self, **search_params) -> Iterable[MODEL]:
        """Find models using filters

        E.g.
        find(name="John") finds all models with name = John

        :param search_params: Any keyword argument to be used as equality filter
        :return: A collection of models
        :rtype: Iterable
        """
        stmt = select(self._model)  # type: ignore
        stmt = self._filter_select(stmt, **search_params)

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

    def _is_mapped_object(self, obj: object) -> TypeGuard[MODEL]:
        """Checks if the object is handled by the repository and is mapped in SQLAlchemy.

        :param obj: a mapped object instance
        :return: True if the
        :rtype: bool
        :raises InvalidModel: when
        """
        # TODO: This is probably redundant, we could do these checks once in __init__
        try:
            object_mapper(obj)
            if isinstance(obj, self._model):
                return True
            raise InvalidModel(f"This repository can handle only `{self._model}` models. `{type(obj)}` has been passed.")
        except UnmappedInstanceError:
            return False

    def _is_mapped_property(self, property_name: str) -> bool:
        """Checks if a property is mapped in the model class.

        :param property_name: The name of the property to be evaluated.
        :type property_name: str
        :return: True if the property is mapped.
        :rtype: bool
        """
        m: Mapper = class_mapper(self._model)
        return property_name in m.column_attrs  # type: ignore

    def _filter_select(self, stmt: Select, **search_params) -> Select:
        """Build the query filters from submitted parameters.

        E.g.
        _filter_select(stmt, name="John") adds a `WHERE name = John` statement

        :param stmt: a statement
        :type stmt: Select
        :param search_params: Any keyword argument to be used as equality filter
        :return: The filtered query
        """
        # TODO: Add support for column sorting
        # TODO: Add support for offset/limit
        # TODO: Add support for relationship eager load
        for k, v in search_params.items():
            if not self._is_mapped_property(k):
                raise UnmappedProperty(f"Property `{k}` is not mapped in the ORM for model `{self._model}`")

            stmt = stmt.where(getattr(self._model, k) == v)
        return stmt
