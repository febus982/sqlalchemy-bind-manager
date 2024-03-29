import pytest
from sqlalchemy import Column, String

from sqlalchemy_bind_manager._bind_manager import SQLAlchemyBind
from sqlalchemy_bind_manager.repository import CursorReference


@pytest.fixture
async def model_class_string_pk(sa_bind):
    class MyModel(sa_bind.declarative_base):
        __tablename__ = "mymodel_string_pk"

        model_id = Column(String, primary_key=True)
        name = Column(String)

    if isinstance(sa_bind, SQLAlchemyBind):
        sa_bind.registry_mapper.metadata.create_all(sa_bind.engine)
    else:
        async with sa_bind.engine.begin() as conn:
            await conn.run_sync(sa_bind.registry_mapper.metadata.create_all)

    yield MyModel


def _test_models(model_class):
    return [
        model_class(
            model_id=80,
            name="Someone",
        ),
        model_class(
            model_id=90,
            name="SomeoneElse",
        ),
        model_class(
            model_id=100,
            name="StillSomeoneElse",
        ),
        model_class(
            model_id=110,
            name="NoOne",
        ),
    ]


@pytest.mark.parametrize(
    ["items_per_page", "expected_next_page"],
    [
        [2, True],
        [4, False],
    ],
)
async def test_paginated_find_without_cursor(
    repository_class,
    model_class,
    sa_bind,
    sync_async_wrapper,
    items_per_page,
    expected_next_page,
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many(_test_models(model_class)))

    results = await sync_async_wrapper(
        repo.cursor_paginated_find(
            items_per_page=items_per_page,
        )
    )
    assert len(results.items) == items_per_page
    assert results.items[0].name == "Someone"
    assert results.items[1].name == "SomeoneElse"
    assert results.page_info.items_per_page == items_per_page
    assert results.page_info.total_items == 4
    assert results.page_info.has_next_page is expected_next_page
    assert results.page_info.has_previous_page is False
    assert results.page_info.start_cursor == CursorReference(
        value=results.items[0].model_id, column="model_id"
    )
    assert results.page_info.end_cursor == CursorReference(
        value=results.items[-1].model_id, column="model_id"
    )


async def test_paginated_find_without_query_result(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many(_test_models(model_class)))

    results = await sync_async_wrapper(
        repo.cursor_paginated_find(items_per_page=2, search_params=dict(name="Unknown"))
    )
    assert len(results.items) == 0
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 0
    assert results.page_info.has_next_page is False
    assert results.page_info.has_previous_page is False
    assert results.page_info.start_cursor is None
    assert results.page_info.end_cursor is None


async def test_paginated_find_page_length_after(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many(_test_models(model_class)))

    results = await sync_async_wrapper(
        repo.cursor_paginated_find(
            cursor_reference=CursorReference(
                column="model_id",
                value=80,
            ),
            items_per_page=2,
        )
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 4


async def test_paginated_find_page_length_before(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many(_test_models(model_class)))

    results = await sync_async_wrapper(
        repo.cursor_paginated_find(
            cursor_reference=CursorReference(
                column="model_id",
                value=110,
            ),
            is_before_cursor=True,
            items_per_page=2,
        )
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 4


async def test_paginated_find_max_page_length_is_respected(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    repo._max_query_limit = 2
    await sync_async_wrapper(repo.save_many(_test_models(model_class)))

    results = await sync_async_wrapper(
        repo.cursor_paginated_find(
            cursor_reference=CursorReference(
                column="model_id",
                value=80,
            ),
            items_per_page=50,
        )
    )
    assert len(results.items) == 2
    assert results.items[0].name == "SomeoneElse"
    assert results.items[1].name == "StillSomeoneElse"
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 4


async def test_paginated_find_empty_result(
    repository_class, model_class, sa_bind, sync_async_wrapper
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many(_test_models(model_class)))

    results = await sync_async_wrapper(
        repo.cursor_paginated_find(
            cursor_reference=CursorReference(
                column="model_id",
                value=110,
            ),
            items_per_page=2,
        )
    )
    assert len(results.items) == 0
    assert results.page_info.items_per_page == 2
    assert results.page_info.total_items == 4


@pytest.mark.parametrize(
    ["before", "after", "has_next_page", "has_previous_page", "returned_ids"],
    [
        (None, 75, True, False, [80, 90]),
        (None, 80, True, True, [90, 100]),
        (None, 85, True, True, [90, 100]),
        (None, 90, False, True, [100, 110]),
        (None, 95, False, True, [100, 110]),
        (None, 100, False, True, [110]),
        (None, 105, False, True, [110]),
        (None, 110, False, True, []),
        (None, 115, False, True, []),
        (115, None, False, True, [100, 110]),
        (110, None, True, True, [90, 100]),
        (105, None, True, True, [90, 100]),
        (100, None, True, False, [80, 90]),
        (95, None, True, False, [80, 90]),
        (90, None, True, False, [80]),
        (85, None, True, False, [80]),
        (80, None, True, False, []),
        (75, None, True, False, []),
    ],
)
async def test_paginated_find_previous_next_page(
    repository_class,
    model_class,
    sa_bind,
    sync_async_wrapper,
    before,
    after,
    has_next_page,
    has_previous_page,
    returned_ids,
):
    repo = repository_class(bind=sa_bind, model_class=model_class)
    await sync_async_wrapper(repo.save_many(_test_models(model_class)))

    result = await sync_async_wrapper(
        repo.cursor_paginated_find(
            cursor_reference=CursorReference(
                column="model_id",
                value=after or before,
            ),
            is_before_cursor=bool(before),
            items_per_page=2,
        )
    )

    assert len(returned_ids) == len(result.items)
    if len(returned_ids):
        assert result.page_info.start_cursor == CursorReference(
            value=result.items[0].model_id, column="model_id"
        )
        assert result.page_info.end_cursor == CursorReference(
            value=result.items[-1].model_id, column="model_id"
        )
    for k, v in enumerate(returned_ids):
        assert result.items[k].model_id == v
    assert result.page_info.has_next_page == has_next_page
    assert result.page_info.has_previous_page == has_previous_page


# Lexicographic order here is 100,110,80,90
@pytest.mark.parametrize(
    ["before", "after", "has_next_page", "has_previous_page", "returned_ids"],
    [
        (None, "000", True, False, ["100", "110"]),
        (None, "100", True, True, ["110", "80"]),
        (None, "105", True, True, ["110", "80"]),
        (None, "110", False, True, ["80", "90"]),
        (None, "115", False, True, ["80", "90"]),
        (None, "75", False, True, ["80", "90"]),
        (None, "80", False, True, ["90"]),
        (None, "85", False, True, ["90"]),
        (None, "90", False, True, []),
        (None, "95", False, True, []),
        ("95", None, False, True, ["80", "90"]),
        ("90", None, True, True, ["110", "80"]),
        ("85", None, True, True, ["110", "80"]),
        ("80", None, True, False, ["100", "110"]),
        ("75", None, True, False, ["100", "110"]),
        ("115", None, True, False, ["100", "110"]),
        ("110", None, True, False, ["100"]),
        ("105", None, True, False, ["100"]),
        ("100", None, True, False, []),
        ("000", None, True, False, []),
    ],
)
async def test_paginated_find_string_pk(
    repository_class,
    model_class_string_pk,
    sa_bind,
    sync_async_wrapper,
    before,
    after,
    has_next_page,
    has_previous_page,
    returned_ids,
):
    repo = repository_class(bind=sa_bind, model_class=model_class_string_pk)
    await sync_async_wrapper(repo.save_many(_test_models(model_class_string_pk)))

    result = await sync_async_wrapper(
        repo.cursor_paginated_find(
            cursor_reference=CursorReference(
                column="model_id",
                value=after or before,
            ),
            is_before_cursor=bool(before),
            items_per_page=2,
        )
    )

    assert len(returned_ids) == len(result.items)
    if len(returned_ids):
        assert result.page_info.start_cursor == CursorReference(
            value=result.items[0].model_id, column="model_id"
        )
        assert result.page_info.end_cursor == CursorReference(
            value=result.items[-1].model_id, column="model_id"
        )
    for k, v in enumerate(returned_ids):
        assert result.items[k].model_id == v
    assert result.page_info.has_next_page == has_next_page
    assert result.page_info.has_previous_page == has_previous_page
