import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { ReasoningBlock } from "./reasoning-block";

test("shows a safe reasoning status without exposing raw model rationale", () => {
  render(
    <ReasoningBlock
      capability="run_plan"
      content="用户只发了一个字，我需要先判断他的真实意图"
      isStreaming
    />,
  );

  expect(screen.getByText("正在分析请求…")).toBeVisible();
  expect(screen.getByText("run_plan")).toBeVisible();
  expect(
    screen.queryByText("用户只发了一个字，我需要先判断他的真实意图"),
  ).not.toBeInTheDocument();
});
