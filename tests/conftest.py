import inspect
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Tuple, Type, Union
from uuid import uuid4

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import clear_mappers, relationship

from sqlalchemy_bind_manager import SQLAlchemyAsyncConfig, SQLAlchemyConfig
from sqlalchemy_bind_manager._bind_manager import (
    SQLAlchemyAsyncBind,
    SQLAlchemyBind,
    SQLAlchemyBindManager,
)
from sqlalchemy_bind_manager._repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyRepository,
)
from sqlalchemy_bind_manager._session_handler import AsyncSessionHandler, SessionHandler
from sqlalchemy_bind_manager.repository import AsyncUnitOfWork, UnitOfWork


@pytest.fixture
def single_config():
    return SQLAlchemyConfig(
        engine_url=f"sqlite:///{uuid4()}.db",
        engine_options=dict(connect_args={"check_same_thread": False}),
    )


@pytest.fixture
def multiple_config():
    return {
        "default": SQLAlchemyConfig(
            engine_url=f"sqlite:///{uuid4()}.db",
            engine_options=dict(connect_args={"check_same_thread": False}),
        ),
        "async": SQLAlchemyAsyncConfig(
            engine_url=f"sqlite+aiosqlite:///{uuid4()}.db",
            engine_options=dict(connect_args={"check_same_thread": False}),
        ),
    }


@pytest.fixture()
def sync_async_wrapper():
    """
    Tiny wrapper to allow calling sync and async methods using await.

    :return:
    """

    async def f(call):
        return await call if inspect.iscoroutine(call) else call

    return f


@pytest.fixture()
def sync_async_cm_wrapper():
    """
    Tiny wrapper to allow calling sync and async methods using await.

    :return:
    """

    @asynccontextmanager
    async def f(cm):
        if isinstance(cm, _AsyncGeneratorContextManager):
            async with cm as c:
                yield c
        else:
            with cm as c:
                yield c

    return f


@pytest.fixture
def sa_manager() -> SQLAlchemyBindManager:
    config = {
        "sync": SQLAlchemyConfig(
            engine_url="sqlite://",
            engine_options=dict(connect_args={"check_same_thread": False}),
        ),
        "async": SQLAlchemyAsyncConfig(
            engine_url="sqlite+aiosqlite://",
            engine_options=dict(connect_args={"check_same_thread": False}),
        ),
    }

    yield SQLAlchemyBindManager(config)

    clear_mappers()


@pytest.fixture(params=["sync", "async"])
def sa_bind(request, sa_manager):
    return sa_manager.get_bind(request.param)


@pytest.fixture
async def model_classes(sa_bind) -> Tuple[Type, Type]:
    class ParentModel(sa_bind.declarative_base):
        __tablename__ = "parent_model"
        # required in order to access columns with server defaults
        # or SQL expression defaults, subsequent to a flush, without
        # triggering an expired load
        __mapper_args__ = {"eager_defaults": True}

        model_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String)

        children = relationship(
            "ChildModel",
            back_populates="parent",
            cascade="all, delete-orphan",
            lazy="selectin",
        )

    class ChildModel(sa_bind.declarative_base):
        __tablename__ = "child_model"
        # required in order to access columns with server defaults
        # or SQL expression defaults, subsequent to a flush, without
        # triggering an expired load
        __mapper_args__ = {"eager_defaults": True}

        model_id = Column(Integer, primary_key=True, autoincrement=True)
        parent_model_id = Column(
            Integer, ForeignKey("parent_model.model_id"), nullable=False
        )
        name = Column(String)

        parent = relationship("ParentModel", back_populates="children", lazy="selectin")

    if isinstance(sa_bind, SQLAlchemyBind):
        sa_bind.registry_mapper.metadata.create_all(sa_bind.engine)
    else:
        async with sa_bind.engine.begin() as conn:
            await conn.run_sync(sa_bind.registry_mapper.metadata.create_all)

    return ParentModel, ChildModel


@pytest.fixture
async def model_class(model_classes: Tuple[Type, Type]) -> Type:
    return model_classes[0]


@pytest.fixture
def session_handler_class(sa_bind):
    return (
        AsyncSessionHandler
        if isinstance(sa_bind, SQLAlchemyAsyncBind)
        else SessionHandler
    )


@pytest.fixture
def repository_class(
    sa_bind: Union[SQLAlchemyBind, SQLAlchemyAsyncBind]
) -> Type[Union[SQLAlchemyAsyncRepository, SQLAlchemyRepository]]:
    base_class = (
        SQLAlchemyRepository
        if isinstance(sa_bind, SQLAlchemyBind)
        else SQLAlchemyAsyncRepository
    )

    return base_class


@pytest.fixture
def uow_class(sa_bind):
    return AsyncUnitOfWork if isinstance(sa_bind, SQLAlchemyAsyncBind) else UnitOfWork
