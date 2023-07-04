async def test_paginated_find_page_length(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    model = model_class(
        name="Someone",
    )
    await sync_async_wrapper(repo.save(model))
    model2 = model_class(
        name="SomeoneElse",
    )
    await sync_async_wrapper(repo.save(model2))
    model3 = model_class(
        name="StillSomeoneElse",
    )
    await sync_async_wrapper(repo.save(model3))

    results = await sync_async_wrapper(repo.paginated_find(page=1, items_per_page=2))
    assert len(results.items) == 2
    assert results.items[0].name == "Someone"
    assert results.items[1].name == "SomeoneElse"
    assert results.page_info.page == 1
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 3
    assert results.page_info.total_pages == 2
    assert results.page_info.has_next_page is True
    assert results.page_info.has_previous_page is False


async def test_paginated_find_max_page_length_is_respected(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    repo._max_query_limit = 2
    model = model_class(
        name="Someone",
    )
    await sync_async_wrapper(repo.save(model))
    model2 = model_class(
        name="SomeoneElse",
    )
    await sync_async_wrapper(repo.save(model2))
    model3 = model_class(
        name="StillSomeoneElse",
    )
    await sync_async_wrapper(repo.save(model3))

    results = await sync_async_wrapper(repo.paginated_find(page=1, items_per_page=50))
    assert len(results.items) == 2
    assert results.items[0].name == "Someone"
    assert results.items[1].name == "SomeoneElse"
    assert results.page_info.page == 1
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_pages == 2
    assert results.page_info.total_items == 3
    assert results.page_info.has_next_page is True
    assert results.page_info.has_previous_page is False


async def test_paginated_find_last_page(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    model = model_class(
        name="Someone",
    )
    await sync_async_wrapper(repo.save(model))
    model2 = model_class(
        name="SomeoneElse",
    )
    await sync_async_wrapper(repo.save(model2))
    model3 = model_class(
        name="StillSomeoneElse",
    )
    await sync_async_wrapper(repo.save(model3))

    results = await sync_async_wrapper(repo.paginated_find(page=2, items_per_page=2))
    assert len(results.items) == 1
    assert results.items[0].name == "StillSomeoneElse"
    assert results.page_info.page == 2
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_pages == 2
    assert results.page_info.total_items == 3
    assert results.page_info.has_next_page is False
    assert results.page_info.has_previous_page is True


async def test_paginated_find_after_last_page(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    model = model_class(
        name="Someone",
    )
    await sync_async_wrapper(repo.save(model))
    model2 = model_class(
        name="SomeoneElse",
    )
    await sync_async_wrapper(repo.save(model2))
    model3 = model_class(
        name="StillSomeoneElse",
    )
    await sync_async_wrapper(repo.save(model3))

    results = await sync_async_wrapper(repo.paginated_find(page=4, items_per_page=2))
    assert len(results.items) == 0
    assert results.page_info.page == 0
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_pages == 2
    assert results.page_info.total_items == 3
    assert results.page_info.has_next_page is False


async def test_paginated_find_no_result_filters(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    model = model_class(
        name="Someone",
    )
    await sync_async_wrapper(repo.save(model))
    model2 = model_class(
        name="SomeoneElse",
    )
    await sync_async_wrapper(repo.save(model2))
    model3 = model_class(
        name="StillSomeoneElse",
    )
    await sync_async_wrapper(repo.save(model3))

    results = await sync_async_wrapper(
        repo.paginated_find(page=1, items_per_page=2, search_params={"name": "Goofy"})
    )
    assert len(results.items) == 0
    assert results.page_info.page == 0
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_pages == 0
    assert results.page_info.total_items == 0
    assert results.page_info.has_next_page is False
    assert results.page_info.has_previous_page is False
