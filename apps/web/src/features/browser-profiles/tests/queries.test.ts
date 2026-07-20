import { describe, expect, it, vi } from "vitest";

import { listBrowserProfilePage } from "../api";
import { browserProfileQueries } from "../queries";

vi.mock("../api", () => ({ listBrowserProfilePage: vi.fn() }));

describe("browser profile queries", () => {
  it("owns a project-scoped list key and forwards cancellation", async () => {
    vi.mocked(listBrowserProfilePage).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 10,
      total: 0,
      total_pages: 0,
    });
    const signal = AbortSignal.abort();
    const options = browserProfileQueries.list("project-1");

    expect(options.queryKey).toEqual(["browser-profiles", "project-1", 1, 10]);
    await options.queryFn?.({ signal } as never);
    expect(listBrowserProfilePage).toHaveBeenCalledWith(
      "project-1",
      signal,
      1,
      10,
    );
  });
});
