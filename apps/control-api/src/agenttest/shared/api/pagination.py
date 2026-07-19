from __future__ import annotations

from typing import TypedDict

from fastapi import HTTPException, status

from agenttest.shared.application.pagination import PageRequest, PageResult


class PageMetadata(TypedDict):
    total: int
    page: int
    page_size: int
    total_pages: int


def resolve_page_request(*, page: int | None, page_size: int | None) -> PageRequest | None:
    if page is None and page_size is None:
        return None

    try:
        return PageRequest(
            page=1 if page is None else page,
            page_size=10 if page_size is None else page_size,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


def page_metadata(result: PageResult[object]) -> PageMetadata:
    return {
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "total_pages": result.total_pages,
    }
