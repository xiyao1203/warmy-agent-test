import { describe, expect, it, vi } from "vitest";

import { collectAllPages, type ResourcePage } from "./pagination";

describe("collectAllPages", () => {
  it("collects every server page for complete asset selectors", async () => {
    const fetchPage = vi.fn(
      async (page: number): Promise<ResourcePage<number>> => ({
        items: page === 1 ? [1, 2] : [3],
        page,
        page_size: 50,
        total: 3,
        total_pages: 2,
      }),
    );

    await expect(collectAllPages(fetchPage)).resolves.toEqual([1, 2, 3]);
    expect(fetchPage).toHaveBeenNthCalledWith(1, 1, 50);
    expect(fetchPage).toHaveBeenNthCalledWith(2, 2, 50);
  });
});
