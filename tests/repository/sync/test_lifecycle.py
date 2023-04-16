from unittest.mock import MagicMock

import pytest

from sqlalchemy_bind_manager import SQLAlchemyRepository
from sqlalchemy_bind_manager.exceptions import UnsupportedBind, InvalidConfig


def test_repository_fails_if_not_sync_bind(sync_async_sa_manager):
    class SomeModel:
        pass

    class SyncRepo(SQLAlchemyRepository):
        _model = SomeModel

    with pytest.raises(UnsupportedBind):
        SyncRepo(sync_async_sa_manager.get_bind("async"))


def test_repository_fails_if_both_bind_and_session():
    class SomeModel:
        pass

    class SyncRepo(SQLAlchemyRepository):
        _model = SomeModel

    bind = MagicMock()
    session = MagicMock()
    with pytest.raises(InvalidConfig):
        SyncRepo(bind, session)
