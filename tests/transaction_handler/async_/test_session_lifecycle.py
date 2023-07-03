from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_scoped_session

from sqlalchemy_bind_manager._transaction_handler import AsyncSessionHandler


async def test_session_is_destroyed_on_cleanup(sa_manager):
    uow = AsyncSessionHandler(sa_manager.get_bind())
    original_session_remove = uow._session_class.remove

    with patch.object(
        uow._session_class,
        "remove",
        wraps=original_session_remove,
    ) as mocked_remove:
        # This should trigger the garbage collector and close the session
        uow = None

    mocked_remove.assert_called_once()


def test_session_is_destroyed_on_cleanup_if_loop_is_not_running(sa_manager):
    # Running the test without a loop will trigger the loop creation
    uow = AsyncSessionHandler(sa_manager.get_bind())
    original_session_close = uow._session_class.remove

    with patch.object(
        uow._session_class,
        "remove",
        wraps=original_session_close,
    ) as mocked_close, patch(
        "asyncio.get_event_loop", side_effect=Exception()
    ) as mocked_get_event_loop:
        # This should trigger the garbage collector and close the session
        uow = None

    mocked_get_event_loop.assert_called_once()
    mocked_close.assert_called_once()


@pytest.mark.parametrize("read_only_flag", [True, False])
@patch.object(AsyncSessionHandler, "commit", return_value=None)
async def test_commit_is_called_only_if_not_read_only(
    mocked_uow_commit: AsyncMock,
    read_only_flag,
    repository_class,
    model_class,
    sa_manager,
):
    uow = AsyncSessionHandler(sa_manager.get_bind())

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    async with uow.get_session(read_only=read_only_flag) as _session:
        _session.add(model1)

    assert mocked_uow_commit.call_count == int(not read_only_flag)


@pytest.mark.parametrize("commit_fails", [True, False])
async def test_rollback_is_called_if_commit_fails(
    commit_fails,
    sa_manager,
):
    uow = AsyncSessionHandler(sa_manager.get_bind())

    failure_exception = Exception("Some Error")
    mocked_session = AsyncMock(spec=async_scoped_session)
    uow.session = mocked_session
    if commit_fails:
        mocked_session.commit.side_effect = failure_exception

    try:
        await uow.commit()
    except Exception as e:
        assert commit_fails is True
        assert e == failure_exception

    assert mocked_session.commit.call_count == 1
    assert mocked_session.rollback.call_count == int(commit_fails)
