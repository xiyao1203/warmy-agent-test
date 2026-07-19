export const PAGE_SIZES = [10, 20, 50] as const;

export type PageSize = (typeof PAGE_SIZES)[number];

export function isPageSize(value: number): value is PageSize {
  return PAGE_SIZES.includes(value as PageSize);
}

export function visiblePages(page: number, totalPages: number) {
  if (totalPages <= 5) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }
  const start = Math.min(Math.max(page - 2, 1), totalPages - 4);
  return Array.from({ length: 5 }, (_, index) => start + index);
}
