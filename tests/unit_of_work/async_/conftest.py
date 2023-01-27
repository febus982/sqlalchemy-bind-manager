import os
from uuid import uuid4

import pytest
from sqlalchemy.orm import clear_mappers

from sqlalchemy_bind_manager import SQLAlchemyBindManager, SQLAlchemyAsyncBindConfig


@pytest.fixture
def sa_manager() -> SQLAlchemyBindManager:
    test_db_path = f"./{uuid4()}.db"
    config = SQLAlchemyAsyncBindConfig(
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
