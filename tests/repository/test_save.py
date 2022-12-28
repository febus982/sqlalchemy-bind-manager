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
