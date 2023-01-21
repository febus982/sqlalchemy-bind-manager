import os
from typing import Type, Tuple
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import clear_mappers, relationship

from sqlalchemy_bind_manager import (
    SQLAlchemyBindManager,
    SQLAlchemyRepository,
    SQLAlchemyBindConfig,
)


@pytest.fixture
def sa_manager() -> SQLAlchemyBindManager:
    test_db_path = f"./{uuid4()}.db"
    config = SQLAlchemyBindConfig(
        engine_url=f"sqlite:///{test_db_path}",
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
def repository_class(model_class) -> Type[SQLAlchemyRepository]:
    class MyRepository(SQLAlchemyRepository[model_class]):
        _model = model_class

    return MyRepository


@pytest.fixture
def related_repository_class(related_model_classes) -> Type[SQLAlchemyRepository]:
    class ParentRepository(SQLAlchemyRepository[related_model_classes[0]]):
        _model = related_model_classes[0]

    return ParentRepository


@pytest.fixture
def model_class(sa_manager) -> Type:
    default_bind = sa_manager.get_binds()["default"]

    class MyModel(default_bind.model_declarative_base):
        __tablename__ = "mymodel"

        model_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String)

    default_bind.registry_mapper.metadata.create_all(default_bind.engine)

    return MyModel


@pytest.fixture
def related_model_classes(sa_manager) -> Tuple[Type, Type]:
    default_bind = sa_manager.get_binds()["default"]

    class ParentModel(default_bind.model_declarative_base):
        __tablename__ = "parent_model"

        parent_model_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String)

        children = relationship(
            "ChildModel", back_populates="parent", cascade="all, delete-orphan"
        )

    class ChildModel(default_bind.model_declarative_base):
        __tablename__ = "child_model"

        child_model_id = Column(Integer, primary_key=True, autoincrement=True)
        parent_model_id = Column(
            Integer, ForeignKey("parent_model.parent_model_id"), nullable=False
        )
        name = Column(String)

        parent = relationship("ParentModel", back_populates="children")

    default_bind.registry_mapper.metadata.create_all(default_bind.engine)

    return ParentModel, ChildModel
