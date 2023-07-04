import inspect
import os
from typing import Tuple, Type
from uuid import uuid4

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import clear_mappers, relationship

from sqlalchemy_bind_manager import SQLAlchemyAsyncConfig, SQLAlchemyConfig
from sqlalchemy_bind_manager._bind_manager import SQLAlchemyBind, SQLAlchemyBindManager


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


@pytest.fixture
def sa_manager() -> SQLAlchemyBindManager:
    test_sync_db_path = f"./{uuid4()}.db"
    test_async_db_path = f"./{uuid4()}.db"
    config = {
        "sync": SQLAlchemyConfig(
            engine_url=f"sqlite:///{test_sync_db_path}",
            engine_options=dict(connect_args={"check_same_thread": False}),
        ),
        "async": SQLAlchemyAsyncConfig(
            engine_url=f"sqlite+aiosqlite:///{test_sync_db_path}",
            engine_options=dict(connect_args={"check_same_thread": False}),
        ),
    }

    yield SQLAlchemyBindManager(config)
    try:
        os.unlink(test_sync_db_path)
    except FileNotFoundError:
        pass

    try:
        os.unlink(test_async_db_path)
    except FileNotFoundError:
        pass

    clear_mappers()


@pytest.fixture(params=["sync", "async"])
def sa_bind(request, sa_manager):
    return sa_manager.get_bind(request.param)


@pytest.fixture
async def model_classes(sa_bind) -> Tuple[Type, Type]:
    class ParentModel(sa_bind.model_declarative_base):
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

    class ChildModel(sa_bind.model_declarative_base):
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
