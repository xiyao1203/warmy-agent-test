import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MissionPreviewDetails } from "../mission-confirmation-details";
import { MissionProgressCard } from "../mission-progress-card";

describe("Mission cards", () => {
  it("shows inferred facts, channels, budget and forbidden actions", () => {
    render(
      <MissionPreviewDetails
        mission={{
          mission_id: "mission-1",
          project_id: "project-1",
          session_id: "session-1",
          status: "ready_for_confirmation",
          active_revision_id: null,
          workflow_id: null,
          facts: {
            test_goal: {
              value: "验证多轮问答",
              source: "system_inferred",
              confidence: 0.75,
              verified: false,
              sensitive: false,
            },
          },
          ready: true,
          missing_inputs: [],
          execution_channels: ["api", "browser", "security"],
          action_allowlist: ["read"],
          inferred_scenarios: ["退款边界"],
          revision_hash: "a".repeat(64),
          snapshot: { budget: { max_cases: 50, hard_cost: 20 } },
          updated_at: "2026-07-12T00:00:00Z",
        }}
      />,
    );

    expect(screen.getByText(/系统推断/)).toBeVisible();
    expect(screen.getByText("API 主回归")).toBeVisible();
    expect(screen.getByText("浏览器关键链路")).toBeVisible();
    expect(screen.getByText("安全基线")).toBeVisible();
    expect(screen.getByText(/最多 50 条用例/)).toBeVisible();
    expect(screen.getByText(/禁止删除、支付、发布和权限变更/)).toBeVisible();
  });

  it("shows mission progress and links the run", () => {
    render(
      <MissionProgressCard
        output={{
          mission_id: "mission-1",
          status: "running",
          run_id: "run-1",
          missing_fields: [],
        }}
        projectId="project-1"
      />,
    );

    expect(screen.getByText("全链路测试执行中")).toBeVisible();
    expect(screen.getByRole("link", { name: "查看运行详情" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs/run-1",
    );
  });
});
