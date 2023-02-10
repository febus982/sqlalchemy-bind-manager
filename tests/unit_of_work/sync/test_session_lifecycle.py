from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import scoped_session

from sqlalchemy_bind_manager._unit_of_work import SQLAlchemyUnitOfWork


def test_session_is_removed_on_cleanup(sa_manager):
    uow = SQLAlchemyUnitOfWork(sa_manager.get_bind())
    original_session_remove = uow._session.remove
    with patch.object(
        uow._session,
        "remove",
        wraps=original_session_remove,
    ) as mocked_remove:
        # This should trigger the garbage collector and close the session
        uow = None

    mocked_remove.assert_called_once()


@pytest.mark.parametrize("commit_flag", [True, False])
@patch.object(SQLAlchemyUnitOfWork, "commit", return_value=None)
def test_commit_is_called_only_if_commit(
    mocked_uow_commit: MagicMock, commit_flag, repository_class, model_class, sa_manager
):
    uow = SQLAlchemyUnitOfWork(sa_manager.get_bind())
    repo1 = repository_class(sa_manager.get_bind())

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    with uow.get_session(commit=commit_flag) as _session:
        repo1.save(model1, session=_session)

    assert mocked_uow_commit.call_count == int(commit_flag)


@pytest.mark.parametrize("commit_fails", [True, False])
def test_rollback_is_called_if_commit_fails(
    commit_fails,
    sa_manager,
):
    uow = SQLAlchemyUnitOfWork(sa_manager.get_bind())

    failure_exception = Exception("Some Error")
    mocked_session = MagicMock(spec=scoped_session)
    if commit_fails:
        mocked_session.commit.side_effect = failure_exception

    try:
        uow.commit(mocked_session)
    except Exception as e:
        assert commit_fails is True
        assert e == failure_exception

    assert mocked_session.commit.call_count == 1
    assert mocked_session.rollback.call_count == int(commit_fails)
