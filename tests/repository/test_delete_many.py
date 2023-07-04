import pytest


async def test_can_delete_by_instance(
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

    results = [x for x in await sync_async_wrapper(repo.find())]
    assert len(results) == 2

    await sync_async_wrapper(repo.delete_many([model]))
    results = [x for x in await sync_async_wrapper(repo.find())]
    assert len(results) == 1
    assert results[0].model_id == 2
    assert results[0].name == "SomeoneElse"


async def test_delete_inexistent_raises_exception(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)

    results = [x for x in await sync_async_wrapper(repo.find())]
    assert len(results) == 0

    with pytest.raises(Exception):
        await sync_async_wrapper(repo.delete_many([4]))

    with pytest.raises(Exception):
        await sync_async_wrapper(
            repo.delete_many(
                [
                    model_class(
                        model_id=823,
                        name="Someone",
                    )
                ]
            )
        )


async def test_relationships_are_respected(
    repository_class, model_classes, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_classes[0])
    children_repo = repository_class(bind=sa_bind, model_class=model_classes[1])

    parent = model_classes[0](
        name="A Parent",
    )
    child = model_classes[1](name="A Child")
    child2 = model_classes[1](name="Another Child")
    parent.children.append(child)
    parent.children.append(child2)
    await sync_async_wrapper(repo.save(parent))

    retrieved_parent = await sync_async_wrapper(repo.get(parent.model_id))
    assert len(retrieved_parent.children) == 2

    await sync_async_wrapper(repo.delete_many([retrieved_parent]))

    assert len(await sync_async_wrapper(children_repo.find())) == 0
    children_retrieve_using_repo = await sync_async_wrapper(children_repo.find())
    assert len(children_retrieve_using_repo) == 0
