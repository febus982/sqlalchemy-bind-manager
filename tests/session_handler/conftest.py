import pytest

from sqlalchemy_bind_manager._bind_manager import SQLAlchemyAsyncBind
from sqlalchemy_bind_manager._session_handler import (
    AsyncSessionHandler,
    SessionHandler,
)


@pytest.fixture
def session_handler_class(sa_bind):
    return (
        AsyncSessionHandler
        if isinstance(sa_bind, SQLAlchemyAsyncBind)
        else SessionHandler
    )
