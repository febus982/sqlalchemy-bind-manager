from dataclasses import dataclass

import pytest

from sqlalchemy_bind_manager._repository import CursorReference
from sqlalchemy_bind_manager._repository.result_presenters import (
    CursorPaginatedResultPresenter,
)


@dataclass
class MyModel:
    model_id: int
    name: str


@pytest.mark.parametrize(["is_before_cursor"], [(True,), (False,)])
def test_fails_if_reference_cursor_wrong_type(is_before_cursor):
    with pytest.raises(TypeError):
        CursorPaginatedResultPresenter.build_result(
            result_items=[MyModel(model_id=1, name="test")],
            total_items_count=10,
            items_per_page=1,
            cursor_reference=CursorReference(column="model_id", value="1"),
            is_before_cursor=is_before_cursor,
        )
