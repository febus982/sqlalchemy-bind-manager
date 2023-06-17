import os
from typing import Tuple, Type
from uuid import uuid4

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import clear_mappers, relationship

from sqlalchemy_bind_manager import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyAsyncRepository,
    SQLAlchemyBindManager,
)


@pytest.fixture
def sa_manager() -> SQLAlchemyBindManager:
    test_db_path = f"./{uuid4()}.db"
    config = SQLAlchemyAsyncConfig(
        engine_url=f"sqlite+aiosqlite:///{test_db_path}",
        engine_options=dict(connect_args={"check_same_thread": False}),
        session_options=dict(expire_on_commit=False),
    )
    yield SQLAlchemyBindManager(config)
    try:
        os.unlink(test_db_path)
    except FileNotFoundError:
        pass

    clear_mappers()


@pytest.fixture
def repository_class(model_class) -> Type[SQLAlchemyAsyncRepository]:
    class MyRepository(SQLAlchemyAsyncRepository[model_class]):
        _model = model_class

    return MyRepository


@pytest.fixture
def repository_class_string_pk(
    model_class_string_pk,
) -> Type[SQLAlchemyAsyncRepository]:
    class MyRepository(SQLAlchemyAsyncRepository[model_class]):
        _model = model_class_string_pk

    return MyRepository


@pytest.fixture
def related_repository_class(related_model_classes) -> Type[SQLAlchemyAsyncRepository]:
    class ParentRepository(SQLAlchemyAsyncRepository[related_model_classes[0]]):
        _model = related_model_classes[0]

    return ParentRepository


@pytest.fixture
async def model_class(sa_manager):
    default_bind = sa_manager.get_bind()

    class MyModel(default_bind.model_declarative_base):
        __tablename__ = "mymodel"

        model_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String)

    async with default_bind.engine.begin() as conn:
        await conn.run_sync(default_bind.registry_mapper.metadata.create_all)

    yield MyModel


@pytest.fixture
async def model_class_string_pk(sa_manager):
    default_bind = sa_manager.get_bind()

    class MyModel(default_bind.model_declarative_base):
        __tablename__ = "mymodel_string_pk"

        model_id = Column(String, primary_key=True)
        name = Column(String)

    async with default_bind.engine.begin() as conn:
        await conn.run_sync(default_bind.registry_mapper.metadata.create_all)

    yield MyModel


@pytest.fixture
async def related_model_classes(sa_manager) -> Tuple[Type, Type]:
    default_bind = sa_manager.get_bind()

    class ParentModel(default_bind.model_declarative_base):
        __tablename__ = "parent_model"
        # required in order to access columns with server defaults
        # or SQL expression defaults, subsequent to a flush, without
        # triggering an expired load
        __mapper_args__ = {"eager_defaults": True}

        parent_model_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String)

        children = relationship(
            "ChildModel",
            back_populates="parent",
            cascade="all, delete-orphan",
            lazy="selectin",
        )

    class ChildModel(default_bind.model_declarative_base):
        __tablename__ = "child_model"
        # required in order to access columns with server defaults
        # or SQL expression defaults, subsequent to a flush, without
        # triggering an expired load
        __mapper_args__ = {"eager_defaults": True}

        child_model_id = Column(Integer, primary_key=True, autoincrement=True)
        parent_model_id = Column(
            Integer, ForeignKey("parent_model.parent_model_id"), nullable=False
        )
        name = Column(String)

        parent = relationship(
            "ParentModel",
            back_populates="children",
            lazy="selectin",
        )

    async with default_bind.engine.begin() as conn:
        await conn.run_sync(default_bind.registry_mapper.metadata.create_all)

    return ParentModel, ChildModel
