from unittest.mock import patch

import pytest

from sqlalchemy_bind_manager import SQLAlchemyAsyncRepository
from sqlalchemy_bind_manager.exceptions import UnsupportedBind


async def test_session_is_destroyed_on_cleanup(repository_class, sa_manager):
    repo = repository_class(sa_manager)
    original_session_close = repo._session.close

    with patch.object(
        repo._session,
        "close",
        wraps=original_session_close,
    ) as mocked_close:
        # This should trigger the garbage collector and close the session
        repo = None

    mocked_close.assert_called_once()


def test_session_is_destroyed_on_cleanup_if_loop_is_not_running(
    repository_class, sa_manager
):
    # Running the test without a loop will trigger the loop creation
    repo = repository_class(sa_manager)
    original_session_close = repo._session.close

    with patch.object(
        repo._session,
        "close",
        wraps=original_session_close,
    ) as mocked_close:
        # This should trigger the garbage collector and close the session
        repo = None

    mocked_close.assert_called_once()


def test_repository_fails_if_not_async_bind(sync_async_sa_manager):
    class AsyncRepo(SQLAlchemyAsyncRepository):
        _session = None

    with pytest.raises(UnsupportedBind):
        AsyncRepo(sync_async_sa_manager, "sync")


async def test_model_ops_using_different_sessions(
    repository_class, model_class, sa_manager
):
    """
    This test ensure that, even if the session gets closed after
    each repository operation, we still keep track of model changes,
    and we are able to persist the changes using different session
    objects.
    """
    repo1 = repository_class(sa_manager)
    repo2 = repository_class(sa_manager)
    repo3 = repository_class(sa_manager)
    assert repo1._session is not repo2._session
    assert repo1._session is not repo3._session
    assert repo2._session is not repo3._session

    # Populate a database entry to be used for tests using first repo
    model_1 = model_class(
        name="Someone",
    )
    await repo1.save(model_1)
    assert model_1.model_id is not None

    # Retrieve the model using second repo
    model_2 = await repo2.get(model_1.model_id)
    assert model_2 != model_1
    assert model_2.model_id == model_1.model_id

    # Update the new model
    model_2.name = "SomeoneElse"
    await repo2.save(model_2)

    # Check model has been updated
    updated_model = await repo2.get(model_1.model_id)
    assert updated_model.model_id == model_2.model_id
    assert updated_model.name == "SomeoneElse"

    # Check the model is a different object and original object is unchanged
    assert updated_model != model_2
    assert updated_model != model_1
    assert model_1.name == "Someone"

    # Check we can update the model without retrieving it
    model_1.name = "StillSomeoneElse"
    await repo3.save(model_1)
    model_3 = await repo3.get(model_1.model_id)
    assert model_1.name == "StillSomeoneElse"
    assert model_3.name == "StillSomeoneElse"
    assert model_3 is not model_1
