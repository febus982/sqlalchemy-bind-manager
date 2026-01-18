import asyncio
from multiprocessing.pool import ThreadPool
from time import sleep
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.orm import Session, scoped_session

from sqlalchemy_bind_manager._bind_manager import SQLAlchemyAsyncBind
from sqlalchemy_bind_manager._session_handler import AsyncSessionHandler, SessionHandler


def test_sync_session_is_removed_on_cleanup(sa_manager):
    """Test that sync SessionHandler removes session on garbage collection.

    Note: AsyncSessionHandler does not implement __del__ cleanup because
    async_scoped_session.remove() is an async operation that cannot be
    safely executed during garbage collection.
    """
    sh = SessionHandler(sa_manager.get_bind("sync"))
    original_session_remove = sh.scoped_session.remove

    with patch.object(
        sh.scoped_session,
        "remove",
        wraps=original_session_remove,
    ) as mocked_remove:
        # This should trigger the garbage collector and close the session
        sh = None

    mocked_remove.assert_called_once()


@pytest.mark.parametrize("read_only_flag", [True, False])
async def test_commit_is_called_only_if_not_read_only(
    read_only_flag,
    session_handler_class,
    model_class,
    sa_bind,
    sync_async_cm_wrapper,
):
    sh = session_handler_class(sa_bind)

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )

    with patch.object(
        session_handler_class, "commit", return_value=None
    ) as mocked_sh_commit:
        async with sync_async_cm_wrapper(
            sh.get_session(read_only=read_only_flag)
        ) as _session:
            _session.add(model1)

    assert mocked_sh_commit.call_count == int(not read_only_flag)


@pytest.mark.parametrize("commit_fails", [True, False])
async def test_rollback_is_called_if_commit_fails(
    commit_fails,
    session_handler_class,
    sa_bind,
    sync_async_wrapper,
):
    sh = session_handler_class(sa_bind)

    failure_exception = Exception("Some Error")
    mocked_session = (
        AsyncMock(spec=async_scoped_session)
        if isinstance(sa_bind, SQLAlchemyAsyncBind)
        else MagicMock(spec=scoped_session)
    )
    if commit_fails:
        mocked_session.commit.side_effect = failure_exception

    try:
        await sync_async_wrapper(sh.commit(mocked_session))
    except Exception as e:
        assert commit_fails is True
        assert e == failure_exception

    assert mocked_session.commit.call_count == 1
    assert mocked_session.rollback.call_count == int(commit_fails)


async def test_session_is_different_on_different_asyncio_tasks(sa_manager):
    # Running the test without a loop will trigger the loop creation
    sh = AsyncSessionHandler(sa_manager.get_bind("async"))

    s1 = sh.scoped_session()
    s2 = sh.scoped_session()

    assert isinstance(s1, AsyncSession)
    assert isinstance(s2, AsyncSession)
    assert s1 is s2

    async def _get_sh_session():
        return sh.scoped_session()

    s = await asyncio.gather(
        _get_sh_session(),
        _get_sh_session(),
    )

    assert isinstance(s[0], AsyncSession)
    assert isinstance(s[1], AsyncSession)
    assert s[0] is not s[1]


async def test_session_is_different_on_different_threads(sa_manager):
    # Running the test without a loop will trigger the loop creation
    sh = SessionHandler(sa_manager.get_bind("sync"))

    s1 = sh.scoped_session()
    s2 = sh.scoped_session()

    assert isinstance(s1, Session)
    assert isinstance(s2, Session)
    assert s1 is s2

    def _get_session():
        # This sleep is to make sure the task doesn't
        # resolve immediately and multiple instances
        # end up in different threads
        sleep(1)
        return sh.scoped_session()

    with ThreadPool() as pool:
        s3_task = pool.apply_async(_get_session)
        s4_task = pool.apply_async(_get_session)

        s3 = s3_task.get()
        s4 = s4_task.get()

    assert isinstance(s3, Session)
    assert isinstance(s4, Session)
    assert s3 is not s4
