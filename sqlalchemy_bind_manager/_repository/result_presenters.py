from math import ceil
from typing import List, Union

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
    @classmethod
    def build_result(
        cls,
        result_items: List[MODEL],
        total_items_count: int,
        items_per_page: int,
        cursor_reference: Union[CursorReference, None],
        is_before_cursor: bool,
    ) -> CursorPaginatedResult:
        """
        Produces a structured paginated result identifying previous/next pages
        and slicing results accordingly.

        :param result_items:
        :param total_items_count:
        :param items_per_page:
        :param cursor_reference:
        :param is_before_cursor:
        :return:
        """
        if not result_items:
            return cls._build_empty_items_result(total_items_count, items_per_page)

        if not cursor_reference:
            return cls._build_no_cursor_result(
                result_items, total_items_count, items_per_page
            )

        if is_before_cursor:
            return cls._build_before_cursor_result(
                result_items, total_items_count, items_per_page, cursor_reference
            )

        return cls._build_after_cursor_result(
            result_items, total_items_count, items_per_page, cursor_reference
        )

    @staticmethod
    def _build_empty_items_result(
        total_items_count: int,
        items_per_page: int,
    ) -> CursorPaginatedResult:
        return CursorPaginatedResult(
            items=[],
            page_info=CursorPageInfo(
                items_per_page=items_per_page,
                total_items=total_items_count,
            ),
        )

    @staticmethod
    def _build_no_cursor_result(
        result_items: List[MODEL],
        total_items_count: int,
        items_per_page: int,
    ) -> CursorPaginatedResult:
        has_next_page = len(result_items) > items_per_page
        if has_next_page:
            result_items = result_items[0:items_per_page]
        reference_column = _pk_from_result_object(result_items[0])

        return CursorPaginatedResult(
            items=result_items,
            page_info=CursorPageInfo(
                items_per_page=items_per_page,
                total_items=total_items_count,
                has_previous_page=False,
                has_next_page=has_next_page,
                start_cursor=CursorReference(
                    column=reference_column,
                    value=getattr(result_items[0], reference_column),
                ),
                end_cursor=CursorReference(
                    column=reference_column,
                    value=getattr(result_items[-1], reference_column),
                ),
            ),
        )

    @staticmethod
    def _build_before_cursor_result(
        result_items: List[MODEL],
        total_items_count: int,
        items_per_page: int,
        cursor_reference: CursorReference,
    ) -> CursorPaginatedResult:
        index = -1
        reference_column = cursor_reference.column
        last_found_cursor_value = getattr(result_items[index], reference_column)
        if not isinstance(last_found_cursor_value, type(cursor_reference.value)):
            raise TypeError(
                "Values from CursorReference and results must be of the same type"
            )
        has_next_page = last_found_cursor_value >= cursor_reference.value
        if has_next_page:
            result_items.pop(index)
        has_previous_page = len(result_items) > items_per_page
        if has_previous_page:
            result_items = result_items[-items_per_page:]

        return CursorPaginatedResult(
            items=result_items,
            page_info=CursorPageInfo(
                items_per_page=items_per_page,
                total_items=total_items_count,
                has_previous_page=has_previous_page,
                has_next_page=has_next_page,
                start_cursor=CursorReference(
                    column=reference_column,
                    value=getattr(result_items[0], reference_column),
                )
                if result_items
                else None,
                end_cursor=CursorReference(
                    column=reference_column,
                    value=getattr(result_items[-1], reference_column),
                )
                if result_items
                else None,
            ),
        )

    @staticmethod
    def _build_after_cursor_result(
        result_items: List[MODEL],
        total_items_count: int,
        items_per_page: int,
        cursor_reference: CursorReference,
    ) -> CursorPaginatedResult:
        index = 0
        reference_column = cursor_reference.column
        first_found_cursor_value = getattr(result_items[index], reference_column)
        if not isinstance(first_found_cursor_value, type(cursor_reference.value)):
            raise TypeError(
                "Values from CursorReference and results must be of the same type"
            )
        has_previous_page = first_found_cursor_value <= cursor_reference.value
        if has_previous_page:
            result_items.pop(index)
        has_next_page = len(result_items) > items_per_page
        if has_next_page:
            result_items = result_items[0:items_per_page]

        return CursorPaginatedResult(
            items=result_items,
            page_info=CursorPageInfo(
                items_per_page=items_per_page,
                total_items=total_items_count,
                has_previous_page=has_previous_page,
                has_next_page=has_next_page,
                start_cursor=CursorReference(
                    column=reference_column,
                    value=getattr(result_items[0], reference_column),
                )
                if result_items
                else None,
                end_cursor=CursorReference(
                    column=reference_column,
                    value=getattr(result_items[-1], reference_column),
                )
                if result_items
                else None,
            ),
        )


class PaginatedResultPresenter:
    @staticmethod
    def build_result(
        result_items: List[MODEL],
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
        has_next_page = bool(_page and _page < total_pages)
        has_previous_page = bool(_page and _page > 1)

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
