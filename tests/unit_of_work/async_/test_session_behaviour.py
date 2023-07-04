from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import InvalidRequestError

from sqlalchemy_bind_manager._session_handler import AsyncSessionHandler
from sqlalchemy_bind_manager._unit_of_work import AsyncUnitOfWork


@patch.object(AsyncSessionHandler, "commit", return_value=None)
async def test_commit_triggers_based_on_external_uow_context_manager(
    mocked_uow_commit: MagicMock,
    repository_classes,
    model_classes,
    sa_manager,
):
    uow = AsyncUnitOfWork(sa_manager.get_bind(), repository_classes)
    repo1 = getattr(uow, repository_classes[0].__name__)
    repo2 = getattr(uow, repository_classes[1].__name__)

    # Populate a database entry to be used for tests
    model1 = model_classes[0](
        name="Someone",
    )
    model2 = model_classes[1](
        name="SomeoneElse",
    )
    async with uow.transaction():
        await repo1.save(model1)
        await repo2.save(model2)
    assert mocked_uow_commit.call_count == 1


async def test_models_are_persisted_using_external_uow(
    repository_classes,
    model_classes,
    sa_manager,
):
    uow = AsyncUnitOfWork(sa_manager.get_bind(), repository_classes)
    repo1 = getattr(uow, repository_classes[0].__name__)
    repo2 = getattr(uow, repository_classes[1].__name__)

    # Populate a database entry to be used for tests
    model1 = model_classes[0](
        name="Someone",
    )
    model2 = model_classes[1](
        name="SomeoneElse",
    )
    async with uow.transaction():
        await repo1.save(model1)
        await repo2.save(model2)

    assert model1.name is not None
    assert model1.model_id is not None
    assert model2.model_id is not None


async def test_uow_repository_operations_fail_without_transaction(
    repository_classes,
    model_classes,
    sa_manager,
):
    uow = AsyncUnitOfWork(sa_manager.get_bind(), repository_classes)
    repo1 = getattr(uow, repository_classes[0].__name__)

    # Populate a database entry to be used for tests
    model1 = model_classes[0](
        name="Someone",
    )

    with pytest.raises(InvalidRequestError):
        await repo1.save(model1)


async def test_models_operations_with_external_session(
    repository_classes,
    model_classes,
    sa_manager,
):
    uow = AsyncUnitOfWork(sa_manager.get_bind(), repository_classes)
    repo1 = getattr(uow, repository_classes[0].__name__)
    repo2 = getattr(uow, repository_classes[1].__name__)

    # Populate a database entry to be used for tests
    model1 = model_classes[0](
        name="Someone",
    )
    model2 = model_classes[1](
        name="SomeoneElse",
    )
    async with uow.transaction():
        await repo1.save(model1)
        await repo2.save(model2)

    model1.name = "SomeoneNew"
    model2.name = "SomeoneElseNew"

    async with uow.transaction():
        await repo1.save(model1)

    async with uow.transaction():
        m1new = await repo1.get(model1.model_id)
        m2new = await repo2.get(model2.model_id)

    assert model1 is not m1new
    assert model2 is not m2new
    assert m1new.name == "SomeoneNew"
    assert m2new.name == "SomeoneElse"

    async with uow.transaction(read_only=True):
        m2new.name = "pippo"
        m2updated = await repo2.get(model2.model_id)

    assert m2updated.name != "pippo"
