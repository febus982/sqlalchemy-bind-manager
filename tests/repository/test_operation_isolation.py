from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy_bind_manager._bind_manager import SQLAlchemyAsyncBind
from sqlalchemy_bind_manager._transaction_handler import (
    AsyncSessionHandler,
    SessionHandler,
)


async def test_repository_instance_returns_always_different_models(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo1 = repository_class(bind=sa_bind, model_class=model_class)

    # Populate a database entry to be used for tests using first repo
    model_1 = model_class(
        name="Someone",
    )
    await sync_async_wrapper(repo1.save(model_1))
    assert model_1.model_id is not None

    # Retrieve the model using multiple repos
    retrieved_model_1 = await sync_async_wrapper(repo1.get(model_1.model_id))
    retrieved_model_2 = await sync_async_wrapper(repo1.get(model_1.model_id))
    assert retrieved_model_1 is not model_1
    assert retrieved_model_2 is not model_1
    assert retrieved_model_1.model_id == model_1.model_id
    assert retrieved_model_2.model_id == model_1.model_id


async def test_update_model_doesnt_update_other_models_from_same_repo(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    await sync_async_wrapper(repo.save_many([model1, model2]))
    assert model1.model_id is not None
    assert model2.model_id is not None

    # Retrieve the models
    new_model1 = await sync_async_wrapper(repo.get(model1.model_id))
    new_model2 = await sync_async_wrapper(repo.get(model2.model_id))

    # Update both models but save only model 1
    new_model1.name = "StillSomeoneElse"
    new_model2.name = "IsThisSomeoneElse?"
    await sync_async_wrapper(repo.save(new_model1))

    # Check model1 has been updated
    updated_model1 = await sync_async_wrapper(repo.get(model1.model_id))
    assert updated_model1.name == "StillSomeoneElse"

    # Check model2 has not been updated
    updated_model2 = await sync_async_wrapper(repo.get(model2.model_id))
    assert updated_model2.name == "SomeoneElse"


async def test_update_model_updates_models_retrieved_by_other_repos(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    repo2 = repository_class(bind=sa_bind, model_class=model_class)

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    await sync_async_wrapper(repo.save(model1))
    assert model1.model_id is not None

    # Retrieve the models
    new_model1 = await sync_async_wrapper(repo.get(model1.model_id))

    # Update the model with another repository instance
    new_model1.name = "StillSomeoneElse"
    await sync_async_wrapper(repo2.save(new_model1))

    # Check model1 has been updated
    updated_model1 = await sync_async_wrapper(repo2.get(model1.model_id))
    assert updated_model1.name == "StillSomeoneElse"

    # Check model1 has been updated
    updated_model1b = await sync_async_wrapper(repo.get(model1.model_id))
    assert updated_model1b.name == "StillSomeoneElse"


async def test_commit_triggers_once_per_operation_using_internal_uow(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )

    session_handler_class = (
        AsyncSessionHandler
        if isinstance(sa_bind, SQLAlchemyAsyncBind)
        else SessionHandler
    )
    session_handler_mock = (
        AsyncMock if isinstance(sa_bind, SQLAlchemyAsyncBind) else MagicMock
    )

    with patch.object(
        session_handler_class,
        "commit",
        new_callable=session_handler_mock,
        return_value=None,
    ) as mocked_uow_commit:
        repo1 = repository_class(bind=sa_bind, model_class=model_class)
        repo2 = repository_class(bind=sa_bind, model_class=model_class)
        await sync_async_wrapper(repo1.save(model1))
        await sync_async_wrapper(repo2.save(model2))
    assert mocked_uow_commit.call_count == 2
