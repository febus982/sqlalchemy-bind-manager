from contextlib import AbstractContextManager, AbstractAsyncContextManager
from typing import Dict, Union, Mapping

from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.decl_api import registry

from sqlalchemy_bind_manager.exceptions import NotInitializedBind, UnsupportedBind, InvalidConfig


class SQLAlchemyBindConfig(BaseModel):
    engine_async: bool = False
    engine_options: Union[Mapping, None]
    engine_url: str
    session_options: Union[Mapping, None]


class SQLAlchemyBind(BaseModel):
    bind_async: bool
    engine: Engine
    model_declarative_base: type
    registry_mapper: registry
    session_class: sessionmaker

    class Config:
        arbitrary_types_allowed = True


SQLAlchemyConfig = Union[Dict[str, SQLAlchemyBindConfig], SQLAlchemyBindConfig]


class SQLAlchemyBindManager:
    __binds: Dict[str, SQLAlchemyBind]

    def __init__(self, config: SQLAlchemyConfig) -> None:
        if isinstance(config, SQLAlchemyBindConfig):
            self.__binds = dict(
                default=self.__init_bind("default", config)
            )

        if isinstance(config, dict):
            self.__binds = {}
            for name, conf in config.items():
                self.__binds[name] = self.__init_bind(name, conf)

    def __init_bind(self, name: str, config: SQLAlchemyBindConfig) -> SQLAlchemyBind:
        if not isinstance(config, SQLAlchemyBindConfig):
            raise InvalidConfig(f"Config for bind `{name}` is not a SQLAlchemyBindConfig object")

        engine_options = dict(
            echo=False,
            future=True,
        )
        if engine_options:
            engine_options.update(config.engine_options)

        session_options = dict()
        if session_options:
            session_options.update(config.session_options)

        if config.engine_async:
            engine = create_async_engine(config.engine_url, **engine_options)
        else:
            engine = create_engine(config.engine_url, **engine_options)

        registry_mapper = registry()
        return SQLAlchemyBind(
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

    def get_session(self, bind: str = "default") -> AbstractContextManager[Session]:
        bind = self.__get_bind(bind)
        if not bind.bind_async:
            return bind.session_class()
        else:
            raise UnsupportedBind("Requested bind is asynchronous. Use `get_async_session`")

    def get_async_session(self, bind: str = "default") -> AbstractAsyncContextManager[AsyncSession]:
        bind = self.__get_bind(bind)
        if bind.bind_async:
            return bind.session_class()
        else:
            raise UnsupportedBind("Requested bind is synchronous. Use `get_session`")

    def get_mapper(self, bind: str = "default") -> registry:
        return self.__get_bind(bind).registry_mapper
