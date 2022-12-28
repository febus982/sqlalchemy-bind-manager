from uuid import uuid4

import pytest

from sqlalchemy_bind_manager import SQLAlchemyBindConfig


@pytest.fixture
def single_config():
    return SQLAlchemyBindConfig(
        engine_url=f"sqlite:///{uuid4()}.db",
        engine_options=dict(connect_args={"check_same_thread": False}),
        session_options=dict(expire_on_commit=False),
    )


@pytest.fixture
def multiple_config():
    return {
        "default": SQLAlchemyBindConfig(
            engine_url=f"sqlite:///{uuid4()}.db",
            engine_options=dict(connect_args={"check_same_thread": False}),
            session_options=dict(expire_on_commit=False),
        ),
        "async": SQLAlchemyBindConfig(
            engine_url="postgresql+asyncpg://scott:tiger@localhost/test",
            engine_async=True,
        ),
    }
