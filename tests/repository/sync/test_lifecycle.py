from unittest.mock import MagicMock

import pytest

from sqlalchemy_bind_manager import SQLAlchemyRepository
from sqlalchemy_bind_manager.exceptions import UnsupportedBind, InvalidConfig


def test_repository_fails_if_not_sync_bind(sync_async_sa_manager):
    class SyncRepo(SQLAlchemyRepository):
        pass

    with pytest.raises(UnsupportedBind):
        SyncRepo(sync_async_sa_manager.get_bind("async"))


def test_repository_fails_if_both_bind_and_session():
    class SyncRepo(SQLAlchemyRepository):
        pass

    bind = MagicMock()
    session = MagicMock()
    with pytest.raises(InvalidConfig):
        SyncRepo(bind, session)


# @patch.object(SessionHandler, "commit", return_value=None)
# def test_commit_triggers_only_once_with_external_uow(
#     mocked_uow_commit: MagicMock, repository_class, model_class, sa_manager
# ):
#     uow = SessionHandler(sa_manager.get_bind())
#     repo1 = repository_class(sa_manager.get_bind())
#     repo2 = repository_class(sa_manager.get_bind())
#
#     # Populate a database entry to be used for tests
#     model1 = model_class(
#         name="Someone",
#     )
#     model2 = model_class(
#         name="SomeoneElse",
#     )
#     with uow.get_session() as session:
#         repo1.save(model1, session=session)
#         repo2.save(model2, session=session)
#     assert mocked_uow_commit.call_count == 1
#
#
# def test_models_are_persisted_using_external_uow(
#     repository_class, model_class, sa_manager
# ):
#     uow = SessionHandler(sa_manager.get_bind())
#     repo1 = repository_class(sa_manager.get_bind())
#     repo2 = repository_class(sa_manager.get_bind())
#
#     # Populate a database entry to be used for tests
#     model1 = model_class(
#         name="Someone",
#     )
#     model2 = model_class(
#         name="SomeoneElse",
#     )
#     with uow.get_session() as session:
#         repo1.save(model1, session=session)
#         repo2.save(model2, session=session)
#
#     assert model1.model_id is not None
#     assert model2.model_id is not None
