export const PAGE_SIZES = [10, 20, 50] as const;

export type PageSize = (typeof PAGE_SIZES)[number];

export type ResourcePage<T> = {
  items: T[];
  page: number | null;
  page_size: number;
  total: number;
  total_pages: number;
};

export function normalizeResourcePage<T>(
  value:
    | ResourcePage<T>
    | T[]
    | {
        items: T[];
        page?: number | null;
        page_size?: number;
        total?: number;
        total_pages?: number;
      },
  page: number,
  pageSize: PageSize,
): ResourcePage<T> {
  if (Array.isArray(value)) {
    return {
      items: value,
      page,
      page_size: pageSize,
      total: value.length,
      total_pages: value.length ? 1 : 0,
    };
  }
  return {
    items: value.items,
    page: value.page ?? page,
    page_size: value.page_size ?? pageSize,
    total: value.total ?? value.items.length,
    total_pages:
      value.total_pages ??
      (value.items.length
        ? Math.ceil((value.total ?? value.items.length) / pageSize)
        : 0),
  };
}

export async function collectAllPages<T>(
  fetchPage: (page: number, pageSize: PageSize) => Promise<ResourcePage<T>>,
): Promise<T[]> {
  const first = await fetchPage(1, 50);
  if (first.total_pages <= 1) return first.items;
  const remaining = await Promise.all(
    Array.from({ length: first.total_pages - 1 }, (_, index) =>
      fetchPage(index + 2, 50),
    ),
  );
  return [first, ...remaining].flatMap((page) => page.items);
}

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
