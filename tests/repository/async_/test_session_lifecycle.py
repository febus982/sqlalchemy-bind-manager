from unittest.mock import patch

import pytest

from sqlalchemy_bind_manager import SQLAlchemyAsyncRepository
from sqlalchemy_bind_manager.exceptions import UnsupportedBind


async def test_session_is_destroyed_on_cleanup(repository_class, sa_manager):
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


def test_session_is_destroyed_on_cleanup_if_loop_is_not_running(
    repository_class, sa_manager
):
    # Running the test without a loop will trigger the loop creation
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


def test_repository_fails_if_not_async_bind(sync_async_sa_manager):
    class AsyncRepo(SQLAlchemyAsyncRepository):
        _session = None

    with pytest.raises(UnsupportedBind):
        AsyncRepo(sync_async_sa_manager, "sync")
