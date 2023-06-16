import pytest


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
    model4 = model_class(
        model_id=4,
        name="NoOne",
    )
    repo.save(model4)

    results = repo.cursor_paginated_find(
        order_by="model_id",
        after=1,
        items_per_page=2,
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.items_per_page == 2
    assert results.total_items == 4
    assert results.has_next_page is True
    assert results.has_previous_page is True


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
    model4 = model_class(
        model_id=4,
        name="NoOne",
    )
    repo.save(model4)

    results = repo.cursor_paginated_find(
        order_by="model_id",
        before=4,
        items_per_page=2,
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.items_per_page == 2
    assert results.total_items == 4
    assert results.has_next_page is True
    assert results.has_previous_page is True


def test_paginated_find_must_use_either_after_or_before(
    repository_class, model_class, sa_manager
):
    repo = repository_class(sa_manager.get_bind())
    with pytest.raises(ValueError):
        repo.cursor_paginated_find(
            order_by="model_id",
            after=1,
            before=4,
            items_per_page=2,
        )
    with pytest.raises(ValueError):
        repo.cursor_paginated_find(
            order_by="model_id",
            items_per_page=2,
        )


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
        order_by="model_id",
        after=1,
        items_per_page=50,
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.items_per_page == 2
    assert results.total_items == 3
    assert results.has_next_page is False
    assert results.has_previous_page is True


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
        order_by="model_id",
        after=3,
        items_per_page=2,
    )

    assert len(results.items) == 0
    assert results.items_per_page == 2
    assert results.total_items == 3
    assert results.has_next_page is False
    assert results.has_previous_page is True
