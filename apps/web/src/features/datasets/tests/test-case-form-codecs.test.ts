import { describe, expect, it } from "vitest";

import { recordToRows, rowsToRecord } from "../test-case-form-codecs";

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
});
