import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { usePaginationState } from "./use-pagination-state";

describe("usePaginationState", () => {
  beforeEach(() => {
    window.history.replaceState(
      {},
      "",
      "/projects?status=active&page=2&page_size=20",
    );
  });

  it("reads and writes pagination while preserving filters", () => {
    const { result } = renderHook(() => usePaginationState());

    expect(result.current.page).toBe(2);
    expect(result.current.pageSize).toBe(20);

    act(() => result.current.setPage(3));

    expect(new URLSearchParams(window.location.search).get("status")).toBe(
      "active",
    );
    expect(new URLSearchParams(window.location.search).get("page")).toBe("3");
  });

  it("resets page when page size changes", () => {
    const { result } = renderHook(() => usePaginationState());

    act(() => result.current.setPageSize(50));

    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(50);
  });

  it("supports namespaced detail list state", () => {
    const { result } = renderHook(() => usePaginationState("cases"));

    act(() => result.current.setPage(4));

    expect(new URLSearchParams(window.location.search).get("cases_page")).toBe(
      "4",
    );
    expect(new URLSearchParams(window.location.search).get("page")).toBe("2");
  });
});
