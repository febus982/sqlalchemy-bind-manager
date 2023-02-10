from unittest.mock import patch, AsyncMock

import pytest
from sqlalchemy.ext.asyncio import async_scoped_session

from sqlalchemy_bind_manager._unit_of_work import SQLAlchemyAsyncUnitOfWork


async def test_session_is_destroyed_on_cleanup(sa_manager):
    uow = SQLAlchemyAsyncUnitOfWork(sa_manager.get_bind())
    original_session_remove = uow._session.remove

    with patch.object(
        uow._session,
        "remove",
        wraps=original_session_remove,
    ) as mocked_remove:
        # This should trigger the garbage collector and close the session
        uow = None

    mocked_remove.assert_called_once()


def test_session_is_destroyed_on_cleanup_if_loop_is_not_running(sa_manager):
    # Running the test without a loop will trigger the loop creation
    uow = SQLAlchemyAsyncUnitOfWork(sa_manager.get_bind())
    original_session_close = uow._session.remove

    with patch.object(
        uow._session,
        "remove",
        wraps=original_session_close,
    ) as mocked_close:
        # This should trigger the garbage collector and close the session
        uow = None

    mocked_close.assert_called_once()


@pytest.mark.parametrize("commit_flag", [True, False])
@patch.object(SQLAlchemyAsyncUnitOfWork, "_commit", return_value=None)
async def test_commit_is_called_only_if_commit(
    mocked_uow_commit: AsyncMock, commit_flag, repository_class, model_class, sa_manager
):
    uow = SQLAlchemyAsyncUnitOfWork(sa_manager.get_bind())
    repo1 = repository_class(sa_manager.get_bind())

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    async with uow.get_session(commit=commit_flag) as _session:
        await repo1.save(model1, session=_session)

    assert mocked_uow_commit.call_count == int(commit_flag)


@pytest.mark.parametrize("commit_fails", [True, False])
async def test_rollback_is_called_if_commit_fails(
    commit_fails,
    sa_manager,
):
    uow = SQLAlchemyAsyncUnitOfWork(sa_manager.get_bind())

    failure_exception = Exception("Some Error")
    mocked_session = AsyncMock(spec=async_scoped_session)
    if commit_fails:
        mocked_session.commit.side_effect = failure_exception

    try:
        await uow._commit(mocked_session)
    except Exception as e:
        assert commit_fails is True
        assert e == failure_exception

    assert mocked_session.commit.call_count == 1
    assert mocked_session.rollback.call_count == int(commit_fails)
