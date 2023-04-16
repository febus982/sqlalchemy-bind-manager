from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from sqlalchemy_bind_manager import SQLAlchemyAsyncRepository
from sqlalchemy_bind_manager._transaction_handler import AsyncSessionHandler
from sqlalchemy_bind_manager.exceptions import UnsupportedBind, InvalidConfig


def test_repository_fails_if_not_async_bind(sync_async_sa_manager):
    class SomeModel:
        pass

    class AsyncRepo(SQLAlchemyAsyncRepository):
        _model = SomeModel
        Session = None

    with pytest.raises(UnsupportedBind):
        AsyncRepo(sync_async_sa_manager.get_bind("sync"))


def test_repository_fails_if_both_bind_and_session():
    class SomeModel:
        pass

    class AsyncRepo(SQLAlchemyAsyncRepository):
        _model = SomeModel

    bind = MagicMock()
    session = MagicMock()
    with pytest.raises(InvalidConfig):
        AsyncRepo(bind, session)
