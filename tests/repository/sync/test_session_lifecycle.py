from unittest.mock import patch

import pytest

from sqlalchemy_bind_manager import SQLAlchemySyncRepository
from sqlalchemy_bind_manager.exceptions import UnsupportedBind


def test_session_is_destroyed_on_cleanup(repository_class, sa_manager):
    repo = repository_class(sa_manager)
    original_session_close = repo._session.close

    with patch.object(
        repo._session,
        "close",
        wraps=original_session_close,
    ) as mocked_close:
        # This should trigger the garbage collector and close the session
        repo = None

    mocked_close.assert_called_once()


def test_repository_fails_if_not_sync_bind(sync_async_sa_manager):
    class SyncRepo(SQLAlchemySyncRepository):
        pass

    with pytest.raises(UnsupportedBind):
        SyncRepo(sync_async_sa_manager, "async")
