from unittest.mock import MagicMock, patch

from sqlalchemy_bind_manager._transaction_handler import SessionHandler


def test_repository_instance_return_always_different_models(
    repository_class, model_class, sa_manager
):
    repo1 = repository_class(sa_manager.get_bind())

    # Populate a database entry to be used for tests using first repo
    model_1 = model_class(
        name="Someone",
    )
    repo1.save(model_1)
    assert model_1.model_id is not None

    # Retrieve the model using multiple repos
    retrieved_model_1 = repo1.get(model_1.model_id)
    retrieved_model_2 = repo1.get(model_1.model_id)
    assert retrieved_model_1 is not model_1
    assert retrieved_model_2 is not model_1
    assert retrieved_model_1.model_id == model_1.model_id
    assert retrieved_model_2.model_id == model_1.model_id


def test_update_model_doesnt_update_other_models_from_same_repo(
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
    repo.save_many([model1, model2])
    assert model1.model_id is not None
    assert model2.model_id is not None

    # Retrieve the models
    new_model1 = repo.get(model1.model_id)
    new_model2 = repo.get(model2.model_id)

    # Update both models but save only model 1
    new_model1.name = "StillSomeoneElse"
    new_model2.name = "IsThisSomeoneElse?"
    repo.save(new_model1)

    # Check model1 has been updated
    updated_model1 = repo.get(model1.model_id)
    assert updated_model1.name == "StillSomeoneElse"

    # Check model2 has not been updated
    updated_model2 = repo.get(model2.model_id)
    assert updated_model2.name == "SomeoneElse"


def test_update_model_updates_models_retrieved_by_other_repos(
    repository_class, model_class, sa_manager
):
    repo = repository_class(sa_manager.get_bind())
    repo2 = repository_class(sa_manager.get_bind())

    # Populate a database entry to be used for tests
    model1 = model_class(
        name="Someone",
    )
    repo.save(model1)
    assert model1.model_id is not None

    # Retrieve the models
    new_model1 = repo.get(model1.model_id)

    # Update the model with another repository instance
    new_model1.name = "StillSomeoneElse"
    repo2.save(new_model1)

    # Check model1 has been updated
    updated_model1 = repo2.get(model1.model_id)
    assert updated_model1.name == "StillSomeoneElse"

    # Check model1 has been updated
    updated_model1b = repo.get(model1.model_id)
    assert updated_model1b.name == "StillSomeoneElse"


@patch.object(SessionHandler, "commit", return_value=None)
def test_commit_triggers_once_per_operation(
    mocked_uow_commit: MagicMock, repository_class, model_class, sa_manager
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
    repo1.save(model1)
    repo2.save(model2)
    assert mocked_uow_commit.call_count == 2
