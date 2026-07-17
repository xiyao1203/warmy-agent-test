import { describe, expect, it } from "vitest";

import { parseNumberFieldValue } from "../test-plan-version-fields";

describe("test plan version number fields", () => {
  it("keeps browser number-input conversion semantics", () => {
    expect(parseNumberFieldValue("3")).toBe(3);
    expect(parseNumberFieldValue("0.75")).toBe(0.75);
    expect(parseNumberFieldValue("")).toBe(0);
  });
});
