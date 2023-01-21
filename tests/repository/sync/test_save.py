from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session


def test_save_model(repository_class, model_class, sa_manager):
    model = model_class(
        name="Someone",
    )
    assert model.model_id is None
    repo = repository_class(sa_manager)
    repo.save(model)
    assert model.model_id is not None


def test_save_many_models(repository_class, model_class, sa_manager):
    model = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    assert model.model_id is None
    assert model2.model_id is None
    repo = repository_class(sa_manager)
    repo.save_many({model, model2})
    assert model.model_id is not None
    assert model2.model_id is not None


def test_failed_model_does_rollback_and_reraises_exception(
    repository_class, model_class, sa_manager
):
    class SomeTestException(Exception):
        pass

    with patch.object(
        Session, "rollback", return_value=None
    ) as mocked_rollback, patch.object(
        Session, "commit", side_effect=SomeTestException
    ):
        model = model_class(
            name="Someone",
        )
        repo = repository_class(sa_manager)

        with pytest.raises(SomeTestException):
            repo.save(model)
        mocked_rollback.assert_called_once()


def test_update_model(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager)

    # Populate a database entry to be used for tests
    model = model_class(
        name="Someone",
    )
    repo.save(model)
    assert model.model_id is not None

    # Retrieve the model
    new_model = repo.get(model.model_id)
    assert new_model != model
    assert new_model.model_id == model.model_id

    # Update the new model
    new_model.name = "SomeoneElse"
    repo.save(new_model)

    # Check model has been updated
    updated_model = repo.get(model.model_id)
    assert updated_model != new_model
    assert updated_model.model_id == new_model.model_id
    assert updated_model.name == "SomeoneElse"


def test_nested_models_are_persisted(
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
    repo = related_repository_class(sa_manager)
    repo.save(parent)
    assert parent.parent_model_id is not None
    assert child.child_model_id is not None
    assert child.parent_model_id is not None


def test_nested_models_are_updated(
    related_repository_class, related_model_classes, sa_manager
):
    parent = related_model_classes[0](
        name="A Parent",
    )
    child = related_model_classes[1](name="A Child")
    child2 = related_model_classes[1](name="Another Child")
    parent.children.append(child)
    parent.children.append(child2)
    repo = related_repository_class(sa_manager)
    repo.save(parent)

    retrieved_parent = repo.get(parent.parent_model_id)
    retrieved_parent.children[0].name = "Mario"
    repo.save(retrieved_parent)

    retrieved_parent2 = repo.get(parent.parent_model_id)
    assert retrieved_parent2.children[0].name == "Mario"


def test_nested_models_are_deleted(
    related_repository_class, related_model_classes, sa_manager
):
    parent = related_model_classes[0](
        name="A Parent",
    )
    child = related_model_classes[1](name="A Child")
    child2 = related_model_classes[1](name="Another Child")
    parent.children.append(child)
    parent.children.append(child2)
    repo = related_repository_class(sa_manager)
    repo.save(parent)

    retrieved_parent = repo.get(parent.parent_model_id)
    assert len(retrieved_parent.children) == 2
    retrieved_parent.children.pop(0)
    repo.save(retrieved_parent)

    retrieved_parent2 = repo.get(parent.parent_model_id)
    assert len(retrieved_parent2.children) == 1
