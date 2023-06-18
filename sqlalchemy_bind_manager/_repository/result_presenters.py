from math import ceil
from typing import Collection, List, Union

from sqlalchemy import inspect

from .common import (
    MODEL,
    CursorPageInfo,
    CursorPaginatedResult,
    CursorReference,
    PageInfo,
    PaginatedResult,
)


class CursorPaginatedResultPresenter:
    @staticmethod
    def build_result(
        result_items: List[MODEL],
        total_items_count: int,
        items_per_page: int,
        cursor_reference: Union[CursorReference, None],
        is_end_cursor: bool,
    ) -> CursorPaginatedResult:
        """
        Produces a structured paginated result identifying previous/next pages
        and slicing results accordingly.

        :param result_items:
        :param total_items_count:
        :param items_per_page:
        :param cursor_reference:
        :param is_end_cursor:
        :return:
        """
        result_structure: CursorPaginatedResult = CursorPaginatedResult(
            items=result_items,
            page_info=CursorPageInfo(
                items_per_page=items_per_page,
                total_items=total_items_count,
            ),
        )
        if not result_items:
            return result_structure

        if not cursor_reference:
            has_previous_page = False
            has_next_page = len(result_items) > items_per_page
            if has_next_page:
                result_items = result_items[0:items_per_page]
            result_structure.page_info.has_next_page = has_next_page
            result_structure.page_info.has_previous_page = has_previous_page
            reference_column = _pk_from_result_object(result_items[0])

        elif is_end_cursor:
            index = -1
            reference_column = cursor_reference.column
            last_found_cursor_value = getattr(result_items[index], reference_column)
            """
            Currently we support only numeric or string model values for cursors,
            but pydantic models (cursor) coerce always the value as string.
            This mean if the value is not actually string we need to cast to
            ensure correct ordering is evaluated.
            e.g.
            9 < 10 but '9' > '10' 
            """
            if isinstance(last_found_cursor_value, str):
                has_next_page = last_found_cursor_value >= cursor_reference.value
            else:
                has_next_page = last_found_cursor_value >= float(cursor_reference.value)
            if has_next_page:
                result_items.pop(index)
            has_previous_page = len(result_items) > items_per_page
            if has_previous_page:
                result_items = result_items[-items_per_page:]
        else:
            index = 0
            reference_column = cursor_reference.column
            first_found_cursor_value = getattr(result_items[index], reference_column)
            """
            Currently we support only numeric or string model values for cursors,
            but pydantic models (cursor) coerce always the value as string.
            This mean if the value is not actually string we need to cast to
            ensure correct ordering is evaluated.
            e.g.
            9 < 10 but '9' > '10' 
            """
            if isinstance(first_found_cursor_value, str):
                has_previous_page = first_found_cursor_value <= cursor_reference.value
            else:
                has_previous_page = first_found_cursor_value <= float(
                    cursor_reference.value
                )
            if has_previous_page:
                result_items.pop(index)
            has_next_page = len(result_items) > items_per_page
            if has_next_page:
                result_items = result_items[0:items_per_page]

        result_structure.items = result_items
        result_structure.page_info.has_next_page = has_next_page
        result_structure.page_info.has_previous_page = has_previous_page

        if result_items:
            result_structure.page_info.start_cursor = CursorReference(
                column=reference_column,
                value=getattr(result_items[0], reference_column),
            )
            result_structure.page_info.end_cursor = CursorReference(
                column=reference_column,
                value=getattr(result_items[-1], reference_column),
            )

        return result_structure


class PaginatedResultPresenter:
    @staticmethod
    def build_result(
        result_items: Collection[MODEL],
        total_items_count: int,
        page: int,
        items_per_page: int,
    ) -> PaginatedResult:

        total_pages = (
            0
            if total_items_count == 0 or total_items_count is None
            else ceil(total_items_count / items_per_page)
        )

        _page = 0 if len(result_items) == 0 else min(page, total_pages)
        has_next_page = _page and _page < total_pages
        has_previous_page = _page and _page > 1

        return PaginatedResult(
            items=result_items,
            page_info=PageInfo(
                page=_page,
                items_per_page=items_per_page,
                total_items=total_items_count,
                total_pages=total_pages,
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
            ),
        )


def _pk_from_result_object(model) -> str:
    primary_keys = inspect(type(model)).primary_key  # type: ignore
    if len(primary_keys) > 1:
        raise NotImplementedError("Composite primary keys are not supported.")

    return primary_keys[0].name