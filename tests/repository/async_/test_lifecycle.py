from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from sqlalchemy_bind_manager import SQLAlchemyAsyncRepository
from sqlalchemy_bind_manager._transaction_handler import AsyncSessionHandler
from sqlalchemy_bind_manager.exceptions import UnsupportedBind, InvalidConfig


def test_repository_fails_if_not_async_bind(sync_async_sa_manager):
    class AsyncRepo(SQLAlchemyAsyncRepository):
        Session = None

    with pytest.raises(UnsupportedBind):
        AsyncRepo(sync_async_sa_manager.get_bind("sync"))


def test_repository_fails_if_both_bind_and_session():
    class AsyncRepo(SQLAlchemyAsyncRepository):
        pass

    bind = MagicMock()
    session = MagicMock()
    with pytest.raises(InvalidConfig):
        AsyncRepo(bind, session)


# @patch.object(AsyncSessionHandler, "commit", return_value=None, new_callable=AsyncMock)
# async def test_commit_triggers_only_once_with_external_uow(
#     mocked_uow_commit: AsyncMock, repository_class, model_class, sa_manager
# ):
#     uow = AsyncSessionHandler(sa_manager.get_bind())
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
#     async with uow.get_session() as _session:
#         await repo1.save(model1, session=_session)
#         await repo2.save(model2, session=_session)
#     assert mocked_uow_commit.call_count == 1
#
#
# async def test_models_are_persisted_using_external_uow(
#     repository_class, model_class, sa_manager
# ):
#     uow = AsyncSessionHandler(sa_manager.get_bind())
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
#     async with uow.get_session() as _session:
#         await repo1.save(model1, session=_session)
#         await repo2.save(model2, session=_session)
#
#     assert model1.model_id is not None
#     assert model2.model_id is not None
