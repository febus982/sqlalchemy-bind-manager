import os
from typing import Type, Tuple
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import clear_mappers, relationship

from sqlalchemy_bind_manager import (
    SQLAlchemyBindManager,
    SQLAlchemyRepository,
    SQLAlchemyConfig,
)


@pytest.fixture
def sa_manager() -> SQLAlchemyBindManager:
    test_db_path = f"./{uuid4()}.db"
    config = SQLAlchemyConfig(
        engine_url=f"sqlite:///{test_db_path}",
        engine_options=dict(connect_args={"check_same_thread": False}),
    )
    yield SQLAlchemyBindManager(config)
    try:
        os.unlink(test_db_path)
    except FileNotFoundError:
        pass

    clear_mappers()


@pytest.fixture
def repository_classes(model_classes) -> Tuple[Type[SQLAlchemyRepository], Type[SQLAlchemyRepository]]:
    class MyFirstRepository(SQLAlchemyRepository[model_classes[0]]):
        _model = model_classes[0]

    class MySecondRepository(SQLAlchemyRepository[model_classes[1]]):
        _model = model_classes[1]

    return MyFirstRepository, MySecondRepository


@pytest.fixture
def model_classes(sa_manager) -> Tuple[Type, Type]:
    default_bind = sa_manager.get_bind()

    class MyFirstModel(default_bind.model_declarative_base):
        __tablename__ = "myfirstmodel"
        # required in order to access columns with server defaults
        # or SQL expression defaults, subsequent to a flush, without
        # triggering an expired load
        __mapper_args__ = {"eager_defaults": True}

        model_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String)

    class MySecondModel(default_bind.model_declarative_base):
        __tablename__ = "mysecondmodel"
        # required in order to access columns with server defaults
        # or SQL expression defaults, subsequent to a flush, without
        # triggering an expired load
        __mapper_args__ = {"eager_defaults": True}

        model_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String)

    default_bind.registry_mapper.metadata.create_all(default_bind.engine)

    return MyFirstModel, MySecondModel
