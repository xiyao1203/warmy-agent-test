import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ExperimentList } from "../experiment-list";
import type { ExperimentItem } from "../api";

const api = vi.hoisted(() => ({
  createExperiment: vi.fn(),
  listExperimentRuns: vi.fn(),
  listExperiments: vi.fn(),
  runExperiment: vi.fn(),
}));

vi.mock("../api", () => api);

const experiment: ExperimentItem = {
  baseline_run_ref: {
    href: "/projects/project-1/runs/run-a-123456789",
    id: "run-a-123456789",
    name: "RUN-BASELINE",
    resource_type: "run",
    status: "passed",
  },
  candidate_run_ref: {
    href: "/projects/project-1/runs/run-b-123456789",
    id: "run-b-123456789",
    name: "RUN-CANDIDATE",
    resource_type: "run",
    status: "passed",
  },
  case_count: 8,
  cost_delta: -0.01,
  created_at: "2026-07-01T10:00:00Z",
  description: "v2 对比 v1",
  id: "experiment-1",
  improved_count: 2,
  name: "客服 Agent v2 回归对比",
  project_id: "project-1",
  pass_rate_delta: 0.125,
  regressed_count: 1,
  result_json: {
    case_diffs: [
      {
        category: "degraded",
        duration_delta_ms: 120,
        status_a: "passed",
        status_b: "failed",
        test_case_id: "case-1",
      },
    ],
    summary: {
      avg_duration_delta_ms: 80,
      degraded: 1,
      improved: 2,
      p50_duration_delta_ms: 60,
      p95_duration_delta_ms: 120,
      unchanged: 5,
    },
  },
  run_a_id: "run-a-123456789",
  run_b_id: "run-b-123456789",
  score_delta: 0.08,
  status: "completed",
  updated_at: "2026-07-01T10:00:00Z",
};

describe("ExperimentList", () => {
  beforeEach(() => {
    api.createExperiment.mockReset();
    api.listExperimentRuns.mockReset();
    api.listExperiments.mockReset();
    api.runExperiment.mockReset();
  });

  it("shows experiment workflow and downstream links", async () => {
    api.listExperiments.mockResolvedValue([experiment]);

    render(<ExperimentList projectId="project-1" />);

    expect(await screen.findByText("客服 Agent v2 回归对比")).toBeVisible();
    expect(screen.getByText(/对比用例 8 个 · 提升 2 · 退化 1/)).toBeVisible();
    expect(screen.getByRole("link", { name: /RUN-BASELINE/ })).toHaveAttribute(
      "href",
      "/projects/project-1/runs/run-a-123456789",
    );
    expect(screen.getByText("通过率差异 +12.50%")).toBeVisible();
    expect(screen.getByText(/比较提升、退化和耗时变化/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: /1. 完成两次运行/ }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(screen.getByText("2. 创建对比")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /4. 配置发布门禁/ }),
    ).toHaveAttribute("href", "/projects/project-1/gates");
    expect(screen.getByText("查看逐用例提升和退化")).toBeVisible();
    expect(screen.getByRole("link", { name: "配置门禁" })).toHaveAttribute(
      "href",
      "/projects/project-1/gates",
    );
    expect(
      screen.getByRole("link", { name: "查看两次运行结果" }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(screen.getByRole("link", { name: "调整测试计划" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-plans",
    );
  });

  it("guides empty state to runs before creating comparisons", async () => {
    api.listExperiments.mockResolvedValue([]);

    render(<ExperimentList projectId="project-1" />);

    expect(await screen.findByText("暂无实验")).toBeVisible();
    expect(screen.getByText(/完成两次同一测试计划版本的运行/)).toBeVisible();
    expect(screen.getByRole("link", { name: "去运行中心" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs",
    );
  });
});
