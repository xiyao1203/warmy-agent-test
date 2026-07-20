import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import { invalidateRunList, runQueries } from "../queries";

describe("run queries", () => {
  it("uses one project and run scoped key hierarchy", () => {
    expect(runQueries.list("project-1").queryKey).toEqual([
      "runs",
      "project-1",
      1,
      10,
    ]);
    expect(runQueries.cases("project-1", "run-1").queryKey).toEqual([
      "runs",
      "project-1",
      "run-1",
      "cases",
    ]);
  });

  it("invalidates only the owning project list", async () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");

    await invalidateRunList(client, "project-1");

    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["runs", "project-1"],
    });
  });
});
