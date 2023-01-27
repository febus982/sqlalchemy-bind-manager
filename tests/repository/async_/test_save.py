from unittest.mock import patch, AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


async def test_save_model(repository_class, model_class, sa_manager):
    model = model_class(
        name="Someone",
    )
    assert model.model_id is None
    repo = repository_class(sa_manager.get_bind())
    await repo.save(model)
    assert model.model_id is not None


async def test_save_many_models(repository_class, model_class, sa_manager):
    model = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    assert model.model_id is None
    assert model2.model_id is None
    repo = repository_class(sa_manager.get_bind())
    await repo.save_many({model, model2})
    assert model.model_id is not None
    assert model2.model_id is not None


async def test_failed_model_does_rollback_and_reraises_exception(
    repository_class, model_class, sa_manager
):
    class SomeTestException(Exception):
        pass

    with patch.object(
        AsyncSession, "rollback", new_callable=AsyncMock, return_value=None
    ) as mocked_rollback, patch.object(
        AsyncSession, "commit", new_callable=AsyncMock, side_effect=SomeTestException
    ):
        model = model_class(
            name="Someone",
        )
        repo = repository_class(sa_manager.get_bind())

        with pytest.raises(SomeTestException):
            await repo.save(model)
        mocked_rollback.assert_called_once()


async def test_update_model(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())

    # Populate a database entry to be used for tests
    model = model_class(
        name="Someone",
    )
    await repo.save(model)
    assert model.model_id is not None

    # Retrieve the model
    new_model = await repo.get(model.model_id)
    assert new_model != model
    assert new_model.model_id == model.model_id

    # Update the new model
    new_model.name = "SomeoneElse"
    await repo.save(new_model)

    # Check model has been updated
    updated_model = await repo.get(model.model_id)
    assert updated_model != new_model
    assert updated_model.model_id == new_model.model_id
    assert updated_model.name == "SomeoneElse"


async def test_nested_models_are_persisted(
    related_repository_class, related_model_classes, sa_manager
):
    parent = related_model_classes[0](
        name="A Parent",
    )
    child = related_model_classes[1](name="A Child")
    parent.children.append(child)
    assert parent.parent_model_id is None
    assert child.child_model_id is None
    assert child.parent_model_id is None
    repo = related_repository_class(sa_manager.get_bind())
    await repo.save(parent)
    assert parent.parent_model_id is not None
    assert child.child_model_id is not None
    assert child.parent_model_id is not None


async def test_nested_models_are_updated(
    related_repository_class, related_model_classes, sa_manager
):
    parent = related_model_classes[0](
        name="A Parent",
    )
    child = related_model_classes[1](name="A Child")
    child2 = related_model_classes[1](name="Another Child")
    parent.children.append(child)
    parent.children.append(child2)
    repo = related_repository_class(sa_manager.get_bind())
    await repo.save(parent)

    retrieved_parent = await repo.get(parent.parent_model_id)
    retrieved_parent.children[0].name = "Mario"
    await repo.save(retrieved_parent)

    retrieved_parent2 = await repo.get(parent.parent_model_id)
    assert retrieved_parent2.children[0].name == "Mario"


async def test_nested_models_are_deleted(
    related_repository_class, related_model_classes, sa_manager
):
    parent = related_model_classes[0](
        name="A Parent",
    )
    child = related_model_classes[1](name="A Child")
    child2 = related_model_classes[1](name="Another Child")
    parent.children.append(child)
    parent.children.append(child2)
    repo = related_repository_class(sa_manager.get_bind())
    await repo.save(parent)

    retrieved_parent = await repo.get(parent.parent_model_id)
    assert len(retrieved_parent.children) == 2
    retrieved_parent.children.pop(0)
    await repo.save(retrieved_parent)

    retrieved_parent2 = await repo.get(parent.parent_model_id)
    assert len(retrieved_parent2.children) == 1