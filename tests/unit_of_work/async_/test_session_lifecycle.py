from unittest.mock import patch

from sqlalchemy_bind_manager._unit_of_work import SAAsyncUnitOfWork


async def test_session_is_destroyed_on_cleanup(sa_manager):
    uow = SAAsyncUnitOfWork(sa_manager)
    original_session_remove = uow.Session.remove

    with patch.object(
        uow.Session,
        "remove",
        wraps=original_session_remove,
    ) as mocked_remove:
        # This should trigger the garbage collector and close the session
        uow = None

    mocked_remove.assert_called_once()


def test_session_is_destroyed_on_cleanup_if_loop_is_not_running(sa_manager):
    # Running the test without a loop will trigger the loop creation
    uow = SAAsyncUnitOfWork(sa_manager)
    original_session_close = uow.Session.remove

    with patch.object(
        uow.Session,
        "remove",
        wraps=original_session_close,
    ) as mocked_close:
        # This should trigger the garbage collector and close the session
        uow = None

    mocked_close.assert_called_once()
