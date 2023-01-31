from typing import Union, Mapping, MutableMapping

from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.decl_api import registry

from sqlalchemy_bind_manager.exceptions import (
    NotInitializedBind,
    InvalidConfig,
)


class SQLAlchemyBindConfig(BaseModel):
    engine_options: Union[dict, None]
    engine_url: str
    session_options: Union[dict, None]


class SQLAlchemyAsyncBindConfig(BaseModel):
    engine_options: Union[dict, None]
    engine_url: str
    session_options: Union[dict, None]


class SQLAlchemyBind(BaseModel):
    engine: Engine
    model_declarative_base: type
    registry_mapper: registry
    session_class: sessionmaker[Session]

    class Config:
        arbitrary_types_allowed = True


class SQLAlchemyAsyncBind(BaseModel):
    engine: AsyncEngine
    model_declarative_base: type
    registry_mapper: registry
    session_class: async_sessionmaker[AsyncSession]

    class Config:
        arbitrary_types_allowed = True


SQLAlchemyConfig = Union[
    Mapping[str, Union[SQLAlchemyBindConfig, SQLAlchemyAsyncBindConfig]],
    SQLAlchemyBindConfig,
    SQLAlchemyAsyncBindConfig,
]
DEFAULT_BIND_NAME = "default"


class SQLAlchemyBindManager:
    __binds: MutableMapping[str, Union[SQLAlchemyBind, SQLAlchemyAsyncBind]]

    def __init__(
        self,
        config: SQLAlchemyConfig,
    ) -> None:
        self.__binds = {}
        if isinstance(config, Mapping):
            for name, conf in config.items():
                self.__init_bind(name, conf)
        else:
            self.__init_bind(DEFAULT_BIND_NAME, config)

    def __init_bind(
        self, name: str, config: Union[SQLAlchemyBindConfig, SQLAlchemyAsyncBindConfig]
    ):
        if not any(
            [
                isinstance(config, SQLAlchemyBindConfig),
                isinstance(config, SQLAlchemyAsyncBindConfig),
            ]
        ):
            raise InvalidConfig(
                f"Config for bind `{name}` is not a SQLAlchemyBindConfig or SQLAlchemyAsyncBindConfig object"
            )

        engine_options: dict = config.engine_options or {}
        engine_options.setdefault("echo", False)
        engine_options.setdefault("future", True)

        session_options: dict = config.session_options or {}
        session_options.setdefault("expire_on_commit", False)

        if isinstance(config, SQLAlchemyAsyncBindConfig):
            self.__binds[name] = self.__build_async_bind(
                engine_url=config.engine_url,
                engine_options=engine_options,
                session_options=session_options,
            )
        else:
            self.__binds[name] = self.__build_sync_bind(
                engine_url=config.engine_url,
                engine_options=engine_options,
                session_options=session_options,
            )

    def __build_sync_bind(
        self,
        engine_url: str,
        engine_options: dict,
        session_options: dict,
    ) -> SQLAlchemyBind:
        registry_mapper = registry()
        engine = create_engine(engine_url, **engine_options)
        return SQLAlchemyBind(
            engine=engine,
            registry_mapper=registry_mapper,
            session_class=sessionmaker(
                bind=engine,
                class_=Session,
                **session_options,
            ),
            model_declarative_base=registry_mapper.generate_base(),
        )

    def __build_async_bind(
        self,
        engine_url: str,
        engine_options: dict,
        session_options: dict,
    ) -> SQLAlchemyAsyncBind:
        registry_mapper = registry()
        engine = create_async_engine(engine_url, **engine_options)
        return SQLAlchemyAsyncBind(
            engine=engine,
            registry_mapper=registry_mapper,
            session_class=async_sessionmaker(
                bind=engine,
                **session_options,
            ),
            model_declarative_base=registry_mapper.generate_base(),
        )

    def get_binds(self) -> Mapping[str, Union[SQLAlchemyBind, SQLAlchemyAsyncBind]]:
        return self.__binds

    def get_bind_mappers_metadata(self) -> Mapping[str, MetaData]:
        """
        Returns the mappers metadata in a format that can be used
        in Alembic configuration

        :returns: mappers metadata
        :rtype: dict
        """
        return {k: b.registry_mapper.metadata for k, b in self.__binds.items()}

    def get_bind(
        self, bind_name: str = DEFAULT_BIND_NAME
    ) -> Union[SQLAlchemyBind, SQLAlchemyAsyncBind]:
        try:
            return self.__binds[bind_name]
        except KeyError:
            raise NotInitializedBind("Bind not initialized")

    def get_session(
        self, bind_name: str = DEFAULT_BIND_NAME
    ) -> Union[Session, AsyncSession]:
        return self.get_bind(bind_name).session_class()

    def get_mapper(self, bind_name: str = DEFAULT_BIND_NAME) -> registry:
        return self.get_bind(bind_name).registry_mapper
