import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import { agentQueries, invalidateAgentList } from "../queries";

describe("agent queries", () => {
  it("uses a project-scoped list key", () => {
    expect(agentQueries.list("project-1").queryKey).toEqual([
      "agents",
      "project-1",
      1,
      10,
    ]);
  });

  it("invalidates only the owning project list", async () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");

    await invalidateAgentList(client, "project-1");

    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["agents", "project-1"],
    });
  });
});
