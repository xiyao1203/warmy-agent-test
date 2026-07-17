import { describe, expect, it } from "vitest";

import { datasetQueries } from "../queries";

describe("dataset queries", () => {
  it("uses one hierarchical key space", () => {
    expect(datasetQueries.list("project-1").queryKey).toEqual([
      "datasets",
      "project-1",
    ]);
    expect(
      datasetQueries.cases("project-1", "dataset-1", "version-1").queryKey,
    ).toEqual([
      "datasets",
      "project-1",
      "dataset-1",
      "versions",
      "version-1",
      "cases",
    ]);
  });
});
