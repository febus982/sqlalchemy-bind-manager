async def test_paginated_find_page_length(repository_class, model_class, sa_manager):
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

    results = await repo.paginated_find(page=1, per_page=2)
    assert len(results.items) == 2
    assert results.items[0].name == "Someone"
    assert results.items[1].name == "SomeoneElse"
    assert results.page == 1
    assert results.per_page == 2
    assert results.total_items == 3
    assert results.total_pages == 2


async def test_paginated_find_max_page_length_is_respected(
    repository_class, model_class, sa_manager
):
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

    results = await repo.paginated_find(page=1, per_page=50)
    assert len(results.items) == 2
    assert results.items[0].name == "Someone"
    assert results.items[1].name == "SomeoneElse"
    assert results.page == 1
    assert results.per_page == 2
    assert results.total_pages == 2
    assert results.total_items == 3


async def test_paginated_find_last_page(repository_class, model_class, sa_manager):
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

    results = await repo.paginated_find(page=2, per_page=2)
    assert len(results.items) == 1
    assert results.items[0].name == "StillSomeoneElse"
    assert results.page == 2
    assert results.per_page == 2
    assert results.total_pages == 2
    assert results.total_items == 3


async def test_paginated_find_after_last_page(
    repository_class, model_class, sa_manager
):
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

    results = await repo.paginated_find(page=4, per_page=2)
    assert len(results.items) == 0
    assert results.page == 0
    assert results.per_page == 2
    assert results.total_pages == 2
    assert results.total_items == 3


async def test_paginated_find_no_result_filters(
    repository_class, model_class, sa_manager
):
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

    results = await repo.paginated_find(
        page=1, per_page=2, search_params={"name": "Goofy"}
    )
    assert len(results.items) == 0
    assert results.page == 0
    assert results.per_page == 2
    assert results.total_pages == 0
    assert results.total_items == 0
