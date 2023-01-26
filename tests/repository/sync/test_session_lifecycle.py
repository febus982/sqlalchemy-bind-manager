import pytest

from sqlalchemy_bind_manager import SQLAlchemySyncRepository
from sqlalchemy_bind_manager.exceptions import UnsupportedBind


def test_repository_fails_if_not_sync_bind(sync_async_sa_manager):
    class SyncRepo(SQLAlchemySyncRepository):
        pass

    with pytest.raises(UnsupportedBind):
        SyncRepo(sync_async_sa_manager, "async")


def test_model_ops_using_different_uows(repository_class, model_class, sa_manager):
    """
    This test ensure that, even if the UOW session gets closed after
    each repository operation, we still keep track of model changes,
    and we are able to persist the changes using different session
    objects.
    """
    repo1 = repository_class(sa_manager)
    repo2 = repository_class(sa_manager)
    repo3 = repository_class(sa_manager)
    assert repo1._UOW is not repo2._UOW
    assert repo1._UOW is not repo3._UOW
    assert repo2._UOW is not repo3._UOW

    # Populate a database entry to be used for tests using first repo
    model_1 = model_class(
        name="Someone",
    )
    repo1.save(model_1)
    assert model_1.model_id is not None

    # Retrieve the model using second repo
    model_2 = repo2.get(model_1.model_id)
    assert model_2 != model_1
    assert model_2.model_id == model_1.model_id

    # Update the new model
    model_2.name = "SomeoneElse"
    repo2.save(model_2)

    # Check model has been updated
    updated_model = repo2.get(model_1.model_id)
    assert updated_model.model_id == model_2.model_id
    assert updated_model.name == "SomeoneElse"

    # Check the model is a different object and original object is unchanged
    assert updated_model != model_2
    assert updated_model != model_1
    assert model_1.name == "Someone"

    # Check we can update the model without retrieving it
    model_1.name = "StillSomeoneElse"
    repo3.save(model_1)
    model_3 = repo3.get(model_1.model_id)
    assert model_1.name == "StillSomeoneElse"
    assert model_3.name == "StillSomeoneElse"
    assert model_3 is not model_1


def test_update_model_doesnt_update_other_models_from_same_repo(
    repository_class, model_class, sa_manager
):
    repo = repository_class(sa_manager)

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    repo.save(model1)
    repo.save(model2)
    assert model1.model_id is not None
    assert model2.model_id is not None

    # Retrieve the model
    new_model1 = repo.get(model1.model_id)
    new_model2 = repo.get(model2.model_id)
    assert new_model1 != model1
    assert new_model1.model_id == model1.model_id

    # Update both models
    new_model1.name = "StillSomeoneElse"
    new_model2.name = "IsThisSomeoneElse?"
    repo.save(new_model1)

    # Check model1 has been updated
    updated_model1 = repo.get(model1.model_id)
    assert updated_model1 != new_model1
    assert updated_model1.model_id == new_model1.model_id
    assert updated_model1.name == "StillSomeoneElse"

    # Check model2 has not been updated
    updated_model2 = repo.get(model2.model_id)
    assert updated_model2 != new_model2
    assert updated_model2.model_id == new_model2.model_id
    assert updated_model2.name == "SomeoneElse"
