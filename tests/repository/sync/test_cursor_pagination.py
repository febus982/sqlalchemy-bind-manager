from sqlalchemy_bind_manager import SortDirection


def test_paginated_find_page_length(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    model = model_class(
        model_id=1,
        name="Someone",
    )
    repo.save(model)
    model2 = model_class(
        model_id=2,
        name="SomeoneElse",
    )
    repo.save(model2)
    model3 = model_class(
        model_id=3,
        name="StillSomeoneElse",
    )
    repo.save(model3)

    results = repo.cursor_paginated_find(
        after=("model_id", 1), items_per_page=2
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.page is None
    assert results.items_per_page == 2
    assert results.total_items == 3
    assert results.total_pages == 2


def test_paginated_find_reverse_page_length(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    model = model_class(
        model_id=1,
        name="Someone",
    )
    repo.save(model)
    model2 = model_class(
        model_id=2,
        name="SomeoneElse",
    )
    repo.save(model2)
    model3 = model_class(
        model_id=3,
        name="StillSomeoneElse",
    )
    repo.save(model3)

    results = repo.cursor_paginated_find(
        after=("model_id", 3), items_per_page=2, direction=SortDirection.DESC
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "Someone"
    assert results.page is None
    assert results.items_per_page == 2
    assert results.total_items == 3
    assert results.total_pages == 2


def test_paginated_find_max_page_length_is_respected(
    repository_class, model_class, sa_manager
):
    repo = repository_class(sa_manager.get_bind())
    repo._max_query_limit = 2
    model = model_class(
        name="Someone",
    )
    repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo.save(model3)

    results = repo.cursor_paginated_find(
        after=("model_id", 1), items_per_page=50
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.page is None
    assert results.items_per_page == 2
    assert results.total_pages == 2
    assert results.total_items == 3


def test_paginated_find_after_last_item(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    model = model_class(
        name="Someone",
    )
    repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo.save(model3)

    results = repo.cursor_paginated_find(
        after=("model_id", 3), items_per_page=2
    )
    assert len(results.items) == 0
    assert results.page is None
    assert results.items_per_page == 2
    assert results.total_pages == 2
    assert results.total_items == 3


def test_paginated_find_no_result_filters(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    model = model_class(
        name="Someone",
    )
    repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo.save(model3)

    results = repo.paginated_find(page=1, items_per_page=2, search_params={"name": "Goofy"})
    assert len(results.items) == 0
    assert results.page == 0
    assert results.items_per_page == 2
    assert results.total_pages == 0
    assert results.total_items == 0
