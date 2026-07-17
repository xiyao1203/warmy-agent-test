import { describe, expect, it } from "vitest";

import {
  commaValues,
  optionalInteger,
  optionalPositiveInteger,
} from "../test-case-editor-sections";

describe("test case editor field conversion", () => {
  it("normalizes comma-separated values", () => {
    expect(commaValues(" smoke, payment, , critical ")).toEqual([
      "smoke",
      "payment",
      "critical",
    ]);
  });

  it("accepts only non-negative and positive integer fields", () => {
    expect(optionalInteger("")).toBeUndefined();
    expect(optionalInteger("0")).toBe(0);
    expect(optionalPositiveInteger("1")).toBe(1);
    expect(() => optionalInteger("1.5")).toThrow("执行参数必须是非负整数");
    expect(() => optionalPositiveInteger("0")).toThrow("时长和超时必须大于 0");
  });
});
