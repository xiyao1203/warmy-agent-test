from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil

SUPPORTED_PAGE_SIZES = frozenset({10, 20, 50})


@dataclass(frozen=True, slots=True)
class PageRequest:
    page: int
    page_size: int

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be greater than or equal to 1")
        if self.page_size not in SUPPORTED_PAGE_SIZES:
            raise ValueError("page_size must be one of 10, 20, or 50")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True, slots=True)
class PageResult[T]:
    items: list[T]
    total: int
    page: int
    page_size: int

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("total must be greater than or equal to 0")
        PageRequest(page=self.page, page_size=self.page_size)

    @property
    def total_pages(self) -> int:
        return ceil(self.total / self.page_size) if self.total else 0


def paginate_items[T](items: Sequence[T], page_request: PageRequest) -> PageResult[T]:
    start = page_request.offset
    return PageResult(
        items=list(items[start : start + page_request.page_size]),
        total=len(items),
        page=page_request.page,
        page_size=page_request.page_size,
    )
