from unittest.mock import patch

from sqlalchemy_bind_manager._unit_of_work import SASyncUnitOfWork


def test_session_is_removed_on_cleanup(sa_manager):
    uow = SASyncUnitOfWork(sa_manager.get_bind())
    original_session_remove = uow.Session.remove
    with patch.object(
        uow.Session,
        "remove",
        wraps=original_session_remove,
    ) as mocked_remove:
        # This should trigger the garbage collector and close the session
        uow = None

    mocked_remove.assert_called_once()
