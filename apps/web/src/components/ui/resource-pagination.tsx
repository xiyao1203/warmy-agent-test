"use client";

import {
  ChevronsLeft,
  ChevronsRight,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useEffect } from "react";

import { PAGE_SIZES, type PageSize, visiblePages } from "@/lib/pagination";

import { Pagination, PaginationButton } from "./pagination";
import { Select } from "./select";

type ResourcePaginationProps = {
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: PageSize) => void;
  page: number;
  pageSize: PageSize;
  total: number;
  totalPages: number;
};

export function ResourcePagination({
  onPageChange,
  onPageSizeChange,
  page,
  pageSize,
  total,
  totalPages,
}: ResourcePaginationProps) {
  useEffect(() => {
    if (totalPages > 0 && page > totalPages) onPageChange(totalPages);
  }, [onPageChange, page, totalPages]);
  const empty = totalPages === 0;
  const currentPage = empty ? 0 : Math.min(page, totalPages);
  return (
    <div className="flex min-h-14 flex-wrap items-center justify-between gap-3 border-t border-[var(--hairline)] px-4 py-2.5 text-xs text-[var(--muted)]">
      <span className="shrink-0" data-pagination-total>
        共 {total} 条
      </span>
      <div
        className="ml-auto flex min-w-0 flex-1 flex-wrap items-center justify-end gap-x-3 gap-y-2"
        data-pagination-controls
      >
        <Select
          aria-label="每页条数"
          className="w-28 shrink-0"
          onChange={(event) =>
            onPageSizeChange(Number(event.target.value) as PageSize)
          }
          value={pageSize}
        >
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size} 条/页
            </option>
          ))}
        </Select>
        <span className="shrink-0 whitespace-nowrap">
          第 {currentPage} / {totalPages} 页
        </span>
        <Pagination className="shrink-0">
          <PaginationButton
            aria-label="首页"
            disabled={empty || currentPage <= 1}
            onClick={() => onPageChange(1)}
          >
            <ChevronsLeft aria-hidden="true" className="size-4" />
          </PaginationButton>
          <PaginationButton
            aria-label="上一页"
            disabled={empty || currentPage <= 1}
            onClick={() => onPageChange(currentPage - 1)}
          >
            <ChevronLeft aria-hidden="true" className="size-4" />
          </PaginationButton>
          {visiblePages(currentPage || 1, totalPages).map((value) => (
            <PaginationButton
              active={value === currentPage}
              aria-label={`第 ${value} 页`}
              key={value}
              onClick={() => onPageChange(value)}
            >
              {value}
            </PaginationButton>
          ))}
          <PaginationButton
            aria-label="下一页"
            disabled={empty || currentPage >= totalPages}
            onClick={() => onPageChange(currentPage + 1)}
          >
            <ChevronRight aria-hidden="true" className="size-4" />
          </PaginationButton>
          <PaginationButton
            aria-label="末页"
            disabled={empty || currentPage >= totalPages}
            onClick={() => onPageChange(totalPages)}
          >
            <ChevronsRight aria-hidden="true" className="size-4" />
          </PaginationButton>
        </Pagination>
      </div>
    </div>
  );
}
