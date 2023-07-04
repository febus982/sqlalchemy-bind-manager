from unittest.mock import patch

import pytest
from sqlalchemy.exc import InvalidRequestError


async def test_commit_triggers_based_on_external_uow_context_manager(
    sa_bind,
    repository_class,
    model_classes,
    uow_class,
    session_handler_class,
    sync_async_wrapper,
    sync_async_cm_wrapper,
):
    class RepoClass(repository_class):
        _model = model_classes[0]

    class ChildRepoClass(repository_class):
        _model = model_classes[1]

    repository_classes = [RepoClass, ChildRepoClass]

    with patch.object(
        session_handler_class, "commit", return_value=None
    ) as mocked_uow_commit:
        uow = uow_class(sa_bind, repository_classes)
        repo1 = getattr(uow, repository_classes[0].__name__)
        repo2 = getattr(uow, repository_classes[1].__name__)

        # Populate a database entry to be used for tests
        model1 = model_classes[0](
            name="Someone",
        )
        model2 = model_classes[1](
            name="SomeoneElse",
        )
        async with sync_async_cm_wrapper(uow.transaction()):
            await sync_async_wrapper(repo1.save(model1))
            await sync_async_wrapper(repo2.save(model2))

    assert mocked_uow_commit.call_count == 1


async def test_models_are_persisted_using_external_uow(
    sa_bind,
    repository_class,
    model_classes,
    uow_class,
    sync_async_wrapper,
    sync_async_cm_wrapper,
):
    class RepoClass(repository_class):
        _model = model_classes[0]

    class OtherRepoClass(repository_class):
        _model = model_classes[0]

    repository_classes = [RepoClass, OtherRepoClass]
    uow = uow_class(sa_bind, repository_classes)
    repo1 = getattr(uow, repository_classes[0].__name__)
    repo2 = getattr(uow, repository_classes[1].__name__)

    # Populate a database entry to be used for tests
    model1 = model_classes[0](
        name="Someone",
    )
    model2 = model_classes[0](
        name="SomeoneElse",
    )
    async with sync_async_cm_wrapper(uow.transaction()):
        await sync_async_wrapper(repo1.save(model1))
        await sync_async_wrapper(repo2.save(model2))

    assert model1.name is not None
    assert model1.model_id is not None
    assert model2.model_id is not None


async def test_uow_repository_operations_fail_without_transaction(
    sa_bind,
    repository_class,
    model_classes,
    uow_class,
    sync_async_wrapper,
):
    class RepoClass(repository_class):
        _model = model_classes[0]

    repository_classes = [RepoClass]

    uow = uow_class(sa_bind, repository_classes)
    repo1 = getattr(uow, repository_classes[0].__name__)

    # Populate a database entry to be used for tests
    model1 = model_classes[0](
        name="Someone",
    )

    with pytest.raises(InvalidRequestError):
        await sync_async_wrapper(repo1.save(model1))


async def test_models_operations_with_external_session(
    sa_bind,
    repository_class,
    model_classes,
    uow_class,
    sync_async_wrapper,
    sync_async_cm_wrapper,
):
    class RepoClass(repository_class):
        _model = model_classes[0]

    class OtherRepoClass(repository_class):
        _model = model_classes[0]

    repository_classes = [RepoClass, OtherRepoClass]

    uow = uow_class(sa_bind, repository_classes)
    repo1 = getattr(uow, repository_classes[0].__name__)
    repo2 = getattr(uow, repository_classes[1].__name__)

    # Populate a database entry to be used for tests
    model1 = model_classes[0](
        name="Someone",
    )
    model2 = model_classes[0](
        name="SomeoneElse",
    )
    async with sync_async_cm_wrapper(uow.transaction()):
        await sync_async_wrapper(repo1.save(model1))
        await sync_async_wrapper(repo2.save(model2))

    model1.name = "SomeoneNew"
    model2.name = "SomeoneElseNew"

    async with sync_async_cm_wrapper(uow.transaction()):
        await sync_async_wrapper(repo1.save(model1))

    async with sync_async_cm_wrapper(uow.transaction()):
        m1new = await sync_async_wrapper(repo1.get(model1.model_id))
        m2new = await sync_async_wrapper(repo2.get(model2.model_id))

    assert model1 is not m1new
    assert model2 is not m2new
    assert m1new.name == "SomeoneNew"
    assert m2new.name == "SomeoneElse"

    async with sync_async_cm_wrapper(uow.transaction(read_only=True)):
        m2new.name = "pippo"
        m2updated = await sync_async_wrapper(repo2.get(model2.model_id))

    assert m2updated.name != "pippo"
