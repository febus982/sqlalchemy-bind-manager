async def test_find_limit(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    model = model_class(
        name="Someone",
    )
    await repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    await repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    await repo.save(model3)

    results = [m for m in await repo.find(limit=2)]
    assert len(results) == 2
    assert results[0].name == "Someone"
    assert results[1].name == "SomeoneElse"


async def test_find_max_limit(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    repo._max_query_limit = 2
    model = model_class(
        name="Someone",
    )
    await repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    await repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    await repo.save(model3)

    results = [m for m in await repo.find(limit=50)]
    assert len(results) == 2
    assert results[0].name == "Someone"
    assert results[1].name == "SomeoneElse"


async def test_find_offset(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    model = model_class(
        name="Someone",
    )
    await repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    await repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    await repo.save(model3)

    results = [m for m in await repo.find(limit=2, offset=1)]
    assert len(results) == 2
    assert results[0].name == "SomeoneElse"
    assert results[1].name == "StillSomeoneElse"
