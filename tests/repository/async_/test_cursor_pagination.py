import pytest

from sqlalchemy_bind_manager._repository.common import Cursor


def _test_models(model_class):
    return [
        model_class(
            model_id=10,
            name="Someone",
        ),
        model_class(
            model_id=20,
            name="SomeoneElse",
        ),
        model_class(
            model_id=30,
            name="StillSomeoneElse",
        ),
        model_class(
            model_id=40,
            name="NoOne",
        ),
    ]


@pytest.mark.parametrize(["items_per_page", "expected_next_page"], [
    [2, True],
    [4, False],
])
async def test_paginated_find_without_cursor(
    repository_class, model_class, sa_manager, items_per_page, expected_next_page
):
    repo = repository_class(sa_manager.get_bind())
    await repo.save_many(_test_models(model_class))

    results = await repo.cursor_paginated_find(
        items_per_page=items_per_page,
    )
    assert len(results.items) == items_per_page
    assert results.items[0].name == "Someone"
    assert results.items[1].name == "SomeoneElse"
    assert results.page_info.items_per_page == items_per_page
    assert results.page_info.total_items == 4
    assert results.page_info.has_next_page is expected_next_page
    assert results.page_info.has_previous_page is False
    assert results.page_info.start_cursor == repo.encode_cursor(
        Cursor(value=results.items[0].model_id, column="model_id")
    )
    assert results.page_info.end_cursor == repo.encode_cursor(
        Cursor(value=results.items[-1].model_id, column="model_id")
    )


async def test_paginated_find_page_length_after(
    repository_class, model_class, sa_manager
):
    repo = repository_class(sa_manager.get_bind())
    await repo.save_many(_test_models(model_class))

    results = await repo.cursor_paginated_find(
        reference_cursor=Cursor(
            column="model_id",
            value=10,
        ),
        items_per_page=2,
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 4


async def test_paginated_find_page_length_before(
    repository_class, model_class, sa_manager
):
    repo = repository_class(sa_manager.get_bind())
    await repo.save_many(_test_models(model_class))

    results = await repo.cursor_paginated_find(
        reference_cursor=Cursor(
            column="model_id",
            value=40,
        ),
        is_end_cursor=True,
        items_per_page=2,
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 4


async def test_paginated_find_max_page_length_is_respected(
    repository_class, model_class, sa_manager
):
    repo = repository_class(sa_manager.get_bind())
    repo._max_query_limit = 2
    await repo.save_many(_test_models(model_class))

    results = await repo.cursor_paginated_find(
        reference_cursor=Cursor(
            column="model_id",
            value=10,
        ),
        items_per_page=50,
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 4


async def test_paginated_find_empty_result(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    await repo.save_many(_test_models(model_class))

    results = await repo.cursor_paginated_find(
        reference_cursor=Cursor(
            column="model_id",
            value=40,
        ),
        items_per_page=2,
    )
    assert len(results.items) == 0
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 4


@pytest.mark.parametrize(
    ["before", "after", "has_next_page", "has_previous_page", "returned_ids"],
    [
        (None, 5, True, False, [10, 20]),
        (None, 10, True, True, [20, 30]),
        (None, 15, True, True, [20, 30]),
        (None, 20, False, True, [30, 40]),
        (None, 25, False, True, [30, 40]),
        (None, 30, False, True, [40]),
        (None, 35, False, True, [40]),
        (None, 40, False, True, []),
        (None, 45, False, True, []),
        (45, None, False, True, [30, 40]),
        (40, None, True, True, [20, 30]),
        (35, None, True, True, [20, 30]),
        (30, None, True, False, [10, 20]),
        (25, None, True, False, [10, 20]),
        (20, None, True, False, [10]),
        (15, None, True, False, [10]),
        (10, None, True, False, []),
        (5, None, True, False, []),
    ],
)
async def test_paginated_find_previous_next_page(
    repository_class,
    model_class,
    sa_manager,
    before,
    after,
    has_next_page,
    has_previous_page,
    returned_ids,
):
    repo = repository_class(sa_manager.get_bind())
    await repo.save_many(_test_models(model_class))

    result = await repo.cursor_paginated_find(
        reference_cursor=Cursor(
            column="model_id",
            value=after or before,
        ),
        is_end_cursor=bool(before),
        items_per_page=2,
    )

    assert len(returned_ids) == len(result.items)
    if len(returned_ids):
        assert result.page_info.start_cursor == repo.encode_cursor(
            Cursor(value=result.items[0].model_id, column="model_id")
        )
        assert result.page_info.end_cursor == repo.encode_cursor(
            Cursor(value=result.items[-1].model_id, column="model_id")
        )
    for k, v in enumerate(returned_ids):
        assert result.items[k].model_id == v
    assert result.page_info.has_next_page == has_next_page
    assert result.page_info.has_previous_page == has_previous_page
