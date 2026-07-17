import { describe, expect, it } from "vitest";

import { compactSteps, stepRows } from "../test-case-professional-fields";

describe("professional test case fields", () => {
  it("round-trips a typed browser operation separately from human instructions", () => {
    const source = [
      {
        action: "点击提交并确认页面出现收据",
        expected_result: "收据包含订单 A-100",
        operation: { action: "click" as const, target: "#submit" },
        step_no: 1,
        test_data: { order_id: "A-100" },
      },
    ];

    expect(compactSteps(stepRows(source))).toEqual([
      {
        action: "点击提交并确认页面出现收据",
        artifact_requirements: [],
        assertions: [],
        expected_result: "收据包含订单 A-100",
        operation: { action: "click", target: "#submit" },
        step_no: 1,
        test_data: { order_id: "A-100" },
      },
    ]);
  });
});
