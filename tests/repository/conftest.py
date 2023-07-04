import os
from typing import Iterator, Union
from uuid import uuid4

import pytest
from sqlalchemy.orm import clear_mappers

from sqlalchemy_bind_manager import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyBindManager,
    SQLAlchemyConfig,
)
from sqlalchemy_bind_manager._bind_manager import SQLAlchemyAsyncBind, SQLAlchemyBind
from sqlalchemy_bind_manager._repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyRepository,
)


@pytest.fixture
def sync_async_sa_manager(multiple_config) -> Iterator[SQLAlchemyBindManager]:
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


@pytest.fixture
def repository_class(
    sa_bind: Union[SQLAlchemyBind, SQLAlchemyAsyncBind]
) -> Union[SQLAlchemyAsyncRepository, SQLAlchemyRepository]:
    base_class = (
        SQLAlchemyRepository
        if isinstance(sa_bind, SQLAlchemyBind)
        else SQLAlchemyAsyncRepository
    )

    return base_class
