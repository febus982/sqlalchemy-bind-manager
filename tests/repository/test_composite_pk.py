import os
from typing import Type
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import clear_mappers

from sqlalchemy_bind_manager import (
    SQLAlchemyBindManager,
    SQLAlchemyConfig,
)
from sqlalchemy_bind_manager.repository import SQLAlchemyRepository


@pytest.fixture
def sa_manager() -> SQLAlchemyBindManager:
    test_db_path = f"./{uuid4()}.db"
    config = SQLAlchemyConfig(
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
def model_class_composite_pk(sa_manager) -> Type:
    default_bind = sa_manager.get_bind()

    class MyModel(default_bind.model_declarative_base):
        __tablename__ = "mymodel"
        # required in order to access columns with server defaults
        # or SQL expression defaults, subsequent to a flush, without
        # triggering an expired load
        __mapper_args__ = {"eager_defaults": True}

        model_id = Column(Integer, primary_key=True)
        model_other_id = Column(Integer, primary_key=True)
        name = Column(String)

    default_bind.registry_mapper.metadata.create_all(default_bind.engine)

    return MyModel


@pytest.fixture
def repository_class(model_class_composite_pk) -> Type[SQLAlchemyRepository]:
    class MyRepository(SQLAlchemyRepository[model_class_composite_pk]):
        _model = model_class_composite_pk

    return MyRepository


def test_cannot_use_models_with_composite_pk(repository_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    with pytest.raises(NotImplementedError):
        repo._model_pk()
