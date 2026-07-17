import { describe, expect, it, vi } from "vitest";

import { listBrowserProfiles } from "../api";
import { browserProfileQueries } from "../queries";

vi.mock("../api", () => ({ listBrowserProfiles: vi.fn() }));

describe("browser profile queries", () => {
  it("owns a project-scoped list key and forwards cancellation", async () => {
    vi.mocked(listBrowserProfiles).mockResolvedValue([]);
    const signal = AbortSignal.abort();
    const options = browserProfileQueries.list("project-1");

    expect(options.queryKey).toEqual(["browser-profiles", "project-1"]);
    await options.queryFn?.({ signal } as never);
    expect(listBrowserProfiles).toHaveBeenCalledWith("project-1", signal);
  });
});
