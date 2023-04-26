import os
from typing import Type
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import clear_mappers

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
async def model_class(sa_manager):
    default_bind = sa_manager.get_bind()

    class MyModel(default_bind.model_declarative_base):
        __tablename__ = "mymodel"

        model_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String)

    async with default_bind.engine.begin() as conn:
        await conn.run_sync(default_bind.registry_mapper.metadata.create_all)

    yield MyModel
