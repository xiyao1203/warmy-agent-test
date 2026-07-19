"use client";

import { useCallback, useState } from "react";

import { isPageSize, type PageSize } from "./pagination";

function key(namespace: string | undefined, value: "page" | "page_size") {
  return namespace ? `${namespace}_${value}` : value;
}

function readPositiveInteger(name: string, fallback: number) {
  if (typeof window === "undefined") return fallback;
  const value = Number(new URLSearchParams(window.location.search).get(name));
  return Number.isInteger(value) && value > 0 ? value : fallback;
}

export function usePaginationState(namespace?: string) {
  const pageKey = key(namespace, "page");
  const pageSizeKey = key(namespace, "page_size");
  const [page, setPageState] = useState(() => readPositiveInteger(pageKey, 1));
  const [pageSize, setPageSizeState] = useState<PageSize>(() => {
    const value = readPositiveInteger(pageSizeKey, 10);
    return isPageSize(value) ? value : 10;
  });

  const write = useCallback(
    (nextPage: number, nextPageSize: PageSize) => {
      const params = new URLSearchParams(window.location.search);
      params.set(pageKey, String(nextPage));
      params.set(pageSizeKey, String(nextPageSize));
      window.history.replaceState(
        window.history.state,
        "",
        `${window.location.pathname}?${params.toString()}${window.location.hash}`,
      );
      setPageState(nextPage);
      setPageSizeState(nextPageSize);
    },
    [pageKey, pageSizeKey],
  );

  const setPage = useCallback(
    (value: number) => write(Math.max(1, Math.floor(value)), pageSize),
    [pageSize, write],
  );
  const setPageSize = useCallback(
    (value: PageSize) => write(1, value),
    [write],
  );

  return { page, pageSize, setPage, setPageSize };
}
