from __future__ import annotations

import pytest
from agenttest.shared.api.pagination import resolve_page_request
from agenttest.shared.application.pagination import PageRequest, PageResult
from fastapi import HTTPException


def test_page_request_converts_page_to_offset() -> None:
    request = PageRequest(page=3, page_size=20)

    assert request.offset == 40


@pytest.mark.parametrize("page_size", [10, 20, 50])
def test_page_request_accepts_supported_page_sizes(page_size: int) -> None:
    assert PageRequest(page=1, page_size=page_size).page_size == page_size


@pytest.mark.parametrize(
    ("page", "page_size"),
    [(0, 10), (-1, 10), (1, 1), (1, 25), (1, 100)],
)
def test_page_request_rejects_invalid_values(page: int, page_size: int) -> None:
    with pytest.raises(ValueError):
        PageRequest(page=page, page_size=page_size)


def test_page_result_calculates_total_pages() -> None:
    result = PageResult(items=["item"], total=21, page=2, page_size=10)

    assert result.total_pages == 3


def test_empty_page_result_has_zero_pages() -> None:
    result: PageResult[str] = PageResult(items=[], total=0, page=1, page_size=10)

    assert result.total_pages == 0


def test_optional_page_mode_preserves_legacy_calls() -> None:
    assert resolve_page_request(page=None, page_size=None) is None


def test_optional_page_mode_fills_missing_counterpart() -> None:
    assert resolve_page_request(page=2, page_size=None) == PageRequest(page=2, page_size=10)
    assert resolve_page_request(page=None, page_size=20) == PageRequest(page=1, page_size=20)


@pytest.mark.parametrize(
    ("page", "page_size"),
    [(0, None), (None, 25), (-1, 10)],
)
def test_optional_page_mode_maps_invalid_values_to_http_422(
    page: int | None,
    page_size: int | None,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        resolve_page_request(page=page, page_size=page_size)

    assert exc_info.value.status_code == 422
