import { describe, expect, it } from "vitest";

import { testPlanQueries } from "../queries";

describe("test plan queries", () => {
  it("keeps plan details, versions, and project assets in one hierarchy", () => {
    expect(testPlanQueries.detail("project-1", "plan-1").queryKey).toEqual([
      "test-plans",
      "project-1",
      "plan-1",
    ]);
    expect(testPlanQueries.versions("project-1", "plan-1").queryKey).toEqual([
      "test-plans",
      "project-1",
      "plan-1",
      "versions",
    ]);
    expect(testPlanQueries.assets("project-1").queryKey).toEqual([
      "test-plans",
      "project-1",
      "assets",
    ]);
  });
});
