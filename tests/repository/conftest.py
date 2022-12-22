import os
from typing import Type
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import clear_mappers

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
    os.unlink(test_db_path)
    clear_mappers()


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
def repository_class(model_class) -> Type[SQLAlchemyRepository]:
    class MyRepository(SQLAlchemyRepository[model_class]):
        _model = model_class

    return MyRepository
