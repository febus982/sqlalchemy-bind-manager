from unittest.mock import AsyncMock, patch

from sqlalchemy_bind_manager._transaction_handler import AsyncSessionHandler


async def test_repository_instance_return_always_different_models(
    repository_class, model_class, sa_manager
):
    repo1 = repository_class(sa_manager.get_bind())

    # Populate a database entry to be used for tests using first repo
    model_1 = model_class(
        name="Someone",
    )
    await repo1.save(model_1)
    assert model_1.model_id is not None

    # Retrieve the model using multiple repos
    retrieved_model_1 = await repo1.get(model_1.model_id)
    retrieved_model_2 = await repo1.get(model_1.model_id)
    assert retrieved_model_1 is not model_1
    assert retrieved_model_2 is not model_1
    assert retrieved_model_1.model_id == model_1.model_id
    assert retrieved_model_2.model_id == model_1.model_id


async def test_update_model_doesnt_update_other_models_from_same_repo(
    repository_class, model_class, sa_manager
):
    repo = repository_class(sa_manager.get_bind())

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    await repo.save_many([model1, model2])
    assert model1.model_id is not None
    assert model2.model_id is not None

    # Retrieve the models
    new_model1 = await repo.get(model1.model_id)
    new_model2 = await repo.get(model2.model_id)

    # Update both models but save only model 1
    new_model1.name = "StillSomeoneElse"
    new_model2.name = "IsThisSomeoneElse?"
    await repo.save(new_model1)

    # Check model1 has been updated
    updated_model1 = await repo.get(model1.model_id)
    assert updated_model1.name == "StillSomeoneElse"

    # Check model2 has not been updated
    updated_model2 = await repo.get(model2.model_id)
    assert updated_model2.name == "SomeoneElse"


@patch.object(AsyncSessionHandler, "commit", return_value=None, new_callable=AsyncMock)
async def test_commit_triggers_once_per_operation_using_internal_uow(
    mocked_uow_commit: AsyncMock, repository_class, model_class, sa_manager
):
    repo1 = repository_class(sa_manager.get_bind())
    repo2 = repository_class(sa_manager.get_bind())

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    await repo1.save(model1)
    await repo2.save(model2)
    assert mocked_uow_commit.call_count == 2
