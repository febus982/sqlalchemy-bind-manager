import pytest


async def test_get_returns_model(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    model = model_class(
        model_id=1,
        name="Someone",
    )
    model2 = model_class(
        model_id=2,
        name="SomeoneElse",
    )
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many({model, model2}))

    result = await sync_async_wrapper(repo.get(1))
    assert result.model_id == 1
    assert result.name == "Someone"
    assert isinstance(result, model_class)


async def test_get_many_returns_models(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    model = model_class(
        model_id=1,
        name="Someone",
    )
    model2 = model_class(
        model_id=2,
        name="SomeoneElse",
    )
    model3 = model_class(
        model_id=3,
        name="StillSomeoneElse",
    )
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many({model, model2, model3}))

    result = await sync_async_wrapper(repo.get_many([1, 2]))
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].model_id == 1
    assert result[1].model_id == 2


async def test_get_many_returns_empty_list_if_nothing_found(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)

    result = await sync_async_wrapper(repo.get_many([1, 2]))
    assert isinstance(result, list)
    assert len(result) == 0


async def test_get_raises_exception_if_not_found(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)

    with pytest.raises(Exception):
        await sync_async_wrapper(repo.get(3))
