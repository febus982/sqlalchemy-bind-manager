from sqlalchemy_bind_manager._repository import CursorReference


def test_cursor_reference_doesnt_coerce_values():
    r = CursorReference(
        column="column_name",
        value=10,
    )
    assert isinstance(r.value, int)
