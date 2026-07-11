import { describe, expect, it } from "vitest";

import { executionOutcomePresentation } from "../run-detail";

describe("executionOutcomePresentation", () => {
  it.each([
    ["success", "执行成功", "success"],
    ["awaiting_confirmation", "等待人工确认", "warning"],
    ["auth_expired", "登录态已过期", "danger"],
    ["target_product_error", "目标产品失败", "danger"],
    ["platform_error", "平台执行错误", "danger"],
  ] as const)("maps %s to an actionable label", (outcome, label, tone) => {
    expect(executionOutcomePresentation(outcome)).toEqual({ label, tone });
  });
});
