from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from sqlalchemy_bind_manager._bind_manager import SQLAlchemyAsyncBind


async def test_save_model(repository_class, model_class, sa_bind, sync_async_wrapper):
    model = model_class(
        name="Someone",
    )
    assert model.model_id is None
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save(model))
    assert model.model_id is not None


async def test_save_many_models(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    model = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    assert model.model_id is None
    assert model2.model_id is None
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many({model, model2}))
    assert model.model_id is not None
    assert model2.model_id is not None


async def test_failed_commit_does_rollback_and_reraises_exception(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    class SomeTestError(Exception):
        pass

    model = model_class(
        name="Someone",
    )

    session_class = (
        AsyncSession if isinstance(sa_bind, SQLAlchemyAsyncBind) else Session
    )
    session_mock = AsyncMock if isinstance(sa_bind, SQLAlchemyAsyncBind) else MagicMock

    with (
        patch.object(
            session_class, "rollback", new_callable=session_mock, return_value=None
        ) as mocked_rollback,
        patch.object(
            session_class,
            "commit",
            new_callable=session_mock,
            side_effect=SomeTestError,
        ),
    ):
        repo = repository_class(bind=sa_bind, model_class=model_class)

        with pytest.raises(SomeTestError):
            await sync_async_wrapper(repo.save(model))
        mocked_rollback.assert_called_once()


async def test_update_model(repository_class, model_class, sa_bind, sync_async_wrapper):
    repo = repository_class(bind=sa_bind, model_class=model_class)

    # Populate a database entry to be used for tests
    model = model_class(
        name="Someone",
    )
    await sync_async_wrapper(repo.save(model))
    assert model.model_id is not None

    # Retrieve the model
    new_model = await sync_async_wrapper(repo.get(model.model_id))
    assert new_model != model
    assert new_model.model_id == model.model_id

    # Update the new model
    new_model.name = "SomeoneElse"
    await sync_async_wrapper(repo.save(new_model))

    # Check model has been updated
    updated_model = await sync_async_wrapper(repo.get(model.model_id))
    assert updated_model != new_model
    assert updated_model.model_id == new_model.model_id
    assert updated_model.name == "SomeoneElse"


async def test_nested_models_are_persisted(
    repository_class, model_classes, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_classes[0])
    parent = model_classes[0](name="A Parent")
    child = model_classes[1](name="A Child")
    parent.children.append(child)
    assert parent.model_id is None
    assert child.model_id is None
    assert child.model_id is None

    await sync_async_wrapper(repo.save(parent))

    assert parent.model_id is not None
    assert child.model_id is not None
    assert child.model_id is not None


async def test_nested_models_are_updated(
    repository_class, model_classes, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_classes[0])

    parent = model_classes[0](
        name="A Parent",
    )
    child = model_classes[1](name="A Child")
    child2 = model_classes[1](name="Another Child")
    parent.children.append(child)
    parent.children.append(child2)
    await sync_async_wrapper(repo.save(parent))

    retrieved_parent = await sync_async_wrapper(repo.get(parent.model_id))
    retrieved_parent.children[0].name = "Mario"
    await sync_async_wrapper(repo.save(retrieved_parent))

    retrieved_parent2 = await sync_async_wrapper(repo.get(parent.model_id))
    assert retrieved_parent2.children[0].name == "Mario"


async def test_nested_models_are_deleted(
    repository_class, model_classes, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_classes[0])

    parent = model_classes[0](name="A Parent")
    child = model_classes[1](name="A Child")
    child2 = model_classes[1](name="Another Child")
    parent.children.append(child)
    parent.children.append(child2)
    await sync_async_wrapper(repo.save(parent))

    retrieved_parent = await sync_async_wrapper(repo.get(parent.model_id))
    assert len(retrieved_parent.children) == 2
    retrieved_parent.children.pop(0)
    await sync_async_wrapper(repo.save(retrieved_parent))

    retrieved_parent2 = await sync_async_wrapper(repo.get(parent.model_id))
    assert len(retrieved_parent2.children) == 1
