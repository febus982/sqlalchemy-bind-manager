import pytest

from sqlalchemy_bind_manager.exceptions import UnmappedPropertyError
from sqlalchemy_bind_manager.repository import SortDirection


async def test_find(repository_class, model_class, sa_bind, sync_async_wrapper):
    model = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many({model, model2, model3}))

    results = await sync_async_wrapper(repo.find())
    assert len(results) == 3


async def test_find_filtered(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    model = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many({model, model2, model3}))

    results = await sync_async_wrapper(repo.find(search_params={"name": "Someone"}))
    assert len(results) == 1


async def test_find_filtered_fails_if_invalid_filter(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    with pytest.raises(UnmappedPropertyError):
        await sync_async_wrapper(repo.find(search_params={"somename": "Someone"}))


async def test_find_ordered(repository_class, model_class, sa_bind, sync_async_wrapper):
    model = model_class(
        name="Abbott",
    )
    model2 = model_class(
        name="Costello",
    )
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many({model, model2}))

    results = await sync_async_wrapper(repo.find(order_by=("name",)))
    assert results[0].name == "Abbott"
    assert results[1].name == "Costello"

    results2 = await sync_async_wrapper(
        repo.find(order_by=(("name", SortDirection.ASC),))
    )
    assert results2[0].name == "Abbott"
    assert results2[1].name == "Costello"

    results3 = await sync_async_wrapper(
        repo.find(order_by=(("name", SortDirection.DESC),))
    )
    assert results3[1].name == "Abbott"
    assert results3[0].name == "Costello"


async def test_find_ordered_fails_if_invalid_column(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    with pytest.raises(UnmappedPropertyError):
        await repo.find(order_by=("unexisting",))
    with pytest.raises(UnmappedPropertyError):
        await repo.find(order_by=(("unexisting", SortDirection.DESC),))
