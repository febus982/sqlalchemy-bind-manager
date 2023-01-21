import os
from typing import Iterator
from uuid import uuid4

import pytest
from sqlalchemy.orm import clear_mappers

from sqlalchemy_bind_manager import SQLAlchemyBindConfig, SQLAlchemyBindManager


@pytest.fixture
def sync_async_sa_manager(multiple_config) -> Iterator[SQLAlchemyBindManager]:
    test_sync_db_path = f"./{uuid4()}.db"
    test_async_db_path = f"./{uuid4()}.db"
    config = {
        "sync": SQLAlchemyBindConfig(
            engine_url=f"sqlite:///{test_sync_db_path}",
            engine_options=dict(connect_args={"check_same_thread": False}),
        ),
        "async": SQLAlchemyBindConfig(
            engine_url=f"sqlite+aiosqlite:///{test_sync_db_path}",
            engine_options=dict(connect_args={"check_same_thread": False}),
            engine_async=True,
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
