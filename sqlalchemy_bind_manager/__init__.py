from abc import ABC
from typing import Dict, Union, TypeVar, Generic, Type, Iterable

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
    ModelNotFound, UnmappedProperty,
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


class SQLAlchemyBindManager:
    __binds: Dict[str, SQLAlchemyBind]

    def __init__(self, config: SQLAlchemyConfig) -> None:
        self.__binds = {}
        if isinstance(config, dict):
            for name, conf in config.items():
                self.__init_bind(name, conf)
        else:
            self.__init_bind("default", config)

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

    def __get_bind(self, bind) -> SQLAlchemyBind:
        try:
            return self.__binds[bind]
        except KeyError as err:
            raise NotInitializedBind(f"Bind not initialized")

    def get_session(self, bind: str = "default") -> Session:
        _bind = self.__get_bind(bind)
        if not _bind.bind_async:
            return _bind.session_class()
        else:
            raise UnsupportedBind(
                "Requested bind is asynchronous. Use `get_async_session`"
            )

    def get_async_session(self, bind: str = "default") -> AsyncSession:
        _bind = self.__get_bind(bind)
        if _bind.bind_async:
            return _bind.session_class()
        else:
            raise UnsupportedBind("Requested bind is synchronous. Use `get_session`")

    def get_mapper(self, bind: str = "default") -> registry:
        return self.__get_bind(bind).registry_mapper


class SQLAlchemyRepository(Generic[MODEL], ABC):
    _sa_manager: SQLAlchemyBindManager
    _bind_name: str
    _model: Type[MODEL]

    def __init__(
        self, sa_manager: SQLAlchemyBindManager, bind_name: str = "default"
    ) -> None:
        super().__init__()
        self._sa_manager = sa_manager
        self._bind_name = bind_name

    def _commit(self, session: Union[Session, AsyncSession]):
        try:
            session.commit()
        except:
            session.rollback()
            raise

    def save(self, instance: MODEL) -> MODEL:
        with self._sa_manager.get_session() as session:  # type: ignore
            session.add(instance)
            self._commit(session)
        return instance

    def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        with self._sa_manager.get_session() as session:  # type: ignore
            session.add_all(instances)
            self._commit(session)
        return instances

    def _is_mapped_property(self, property_name: str) -> bool:
        m: Mapper = class_mapper(self._model)
        return property_name in m.column_attrs  # type: ignore

    def _filter_select(self, stmt: Select, **search_params) -> Select:
        for k, v in search_params.items():
            if not self._is_mapped_property(k):
                raise UnmappedProperty(f"Property `{k}` is not mapped in the ORM for model `{self._model}`")

            stmt = stmt.where(getattr(self._model, k) == v)
        return stmt

    def find(self, **search_params) -> Iterable[MODEL]:
        stmt = select(self._model)  # type: ignore
        stmt = self._filter_select(stmt, **search_params)

        with self._sa_manager.get_session() as session:  # type: ignore
            result = session.execute(stmt)
            for model_obj in result.scalars():
                yield model_obj

    def get(self, identifier) -> MODEL:
        with self._sa_manager.get_session() as session:  # type: ignore
            model = session.get(self._model, identifier)
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    def delete(self, entity) -> None:
        obj = entity if self._get_object_mapper(entity) else self.get(entity)
        with self._sa_manager.get_session() as session:  # type: ignore
            session.delete(obj)
            self._commit(session)

    def _get_object_mapper(self, obj) -> Union[None, Mapper]:
        try:
            return object_mapper(obj)
        except UnmappedInstanceError:
            return None
