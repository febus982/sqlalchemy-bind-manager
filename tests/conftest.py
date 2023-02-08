from uuid import uuid4

import pytest

from sqlalchemy_bind_manager import SQLAlchemyConfig, SQLAlchemyAsyncConfig


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
