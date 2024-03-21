import pytest

from sqlalchemy_bind_manager.exceptions import InvalidModelError


async def test_fails_when_saving_models_not_belonging_to_repository(
    repository_class, model_classes, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_classes[0])

    invalid_model = model_classes[1](name="A Child")

    with pytest.raises(InvalidModelError):
        await sync_async_wrapper(repo.save(invalid_model))

    with pytest.raises(InvalidModelError):
        await sync_async_wrapper(repo.save_many([invalid_model]))

    with pytest.raises(InvalidModelError):
        await sync_async_wrapper(repo.delete(invalid_model))

    with pytest.raises(InvalidModelError):
        await sync_async_wrapper(repo.delete_many([invalid_model]))
