import { describe, expect, it } from "vitest";

import {
  assertionsToRows,
  recordToRows,
  rowsToAssertions,
  rowsToRecord,
  rowsToScorers,
  rowsToSecurityPolicies,
  scorersToRows,
  securityPoliciesToRows,
} from "../test-case-form-codecs";

describe("test case form codecs", () => {
  it("preserves boolean and numeric cell values through a row round trip", () => {
    const source = {
      enabled: true,
      retries: 3,
      threshold: 0.75,
    };

    expect(rowsToRecord(recordToRows(source))).toEqual(source);
  });

  it("keeps structured values and trims keys", () => {
    const rows = recordToRows({ nested: { flag: false }, values: [1, "two"] });

    rows[0] = { ...rows[0], key: `  ${rows[0].key}  ` };

    expect(rowsToRecord(rows)).toEqual({
      nested: { flag: false },
      values: [1, "two"],
    });
  });

  it("round-trips every professional rule without discarding extension fields", () => {
    const assertions = [
      { type: "canvas_schema", schema_version: "2" },
      { type: "node_count", min_count: 2 },
      { type: "node_types", required_types: ["text", "image"] },
      {
        from_type: "text",
        to_type: "image",
        type: "required_connection",
      },
      { type: "no_orphan_nodes" },
    ];
    const scorers = [
      {
        config: { rubric: "专业测试标准" },
        threshold: 0.8,
        type: "llm_judge",
      },
    ];
    const securityPolicies = [
      {
        config: { categories: ["identity", "contact"] },
        severity: "high",
        type: "pii_redaction",
      },
    ];

    expect(rowsToAssertions(assertionsToRows(assertions))).toEqual(assertions);
    expect(rowsToScorers(scorersToRows(scorers))).toEqual(scorers);
    expect(
      rowsToSecurityPolicies(securityPoliciesToRows(securityPolicies)),
    ).toEqual(securityPolicies);
  });

  it("merges edited simple fields over the original professional rule", () => {
    const [row] = assertionsToRows([
      { path: "output.status", type: "equals", value: "old", vendor: "v1" },
    ]);

    expect(rowsToAssertions([{ ...row, value: "new" }])).toEqual([
      {
        path: "output.status",
        type: "equals",
        value: "new",
        vendor: "v1",
      },
    ]);
  });
});
