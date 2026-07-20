import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { GateItem, GateRun } from "../api";
import { GateList } from "../gate-list";

const api = vi.hoisted(() => ({
  createGate: vi.fn(),
  deleteGate: vi.fn(),
  evaluateGate: vi.fn(),
  listGateRuns: vi.fn(),
  listGates: vi.fn(),
  listGatePage: vi.fn(),
}));

vi.mock("../api", () => api);

const gate: GateItem = {
  blocking_count: 2,
  cost_limit: 100,
  created_at: "2026-07-04T10:00:00Z",
  critical_cases: ["case-1"],
  enabled: true,
  id: "gate-1",
  evaluated_at: "2026-07-16T09:00:00Z",
  last_decision: "failed",
  last_run_ref: {
    href: "/projects/project-1/runs/run-previous",
    id: "run-previous",
    name: "RUN-PREVIOUS",
    resource_type: "run",
    status: "failed",
  },
  name: "生产发布门禁",
  project_id: "project-1",
  rule_summary: "通过率≥90%，安全分≥80%，关键用例 1 个，成本≤100",
  scope: "project",
  security_threshold: 0.8,
  success_rate_threshold: 0.9,
  updated_at: "2026-07-04T10:00:00Z",
};

const run: GateRun = {
  created_at: "2026-07-04T10:30:00Z",
  id: "run-1",
  status: "completed",
};

describe("GateList", () => {
  beforeEach(() => {
    api.createGate.mockReset();
    api.deleteGate.mockReset();
    api.evaluateGate.mockReset();
    api.listGateRuns.mockReset();
    api.listGates.mockReset();
    api.listGatePage.mockReset();
  });

  it("shows gate evidence links and evaluates a real run", async () => {
    api.listGates.mockResolvedValue([gate]);
    api.listGatePage.mockResolvedValue([gate]);
    api.listGateRuns.mockResolvedValue([run]);
    api.evaluateGate.mockResolvedValue({
      gate_id: gate.id,
      result: { failures: [], passed: true },
    });

    render(<GateList projectId="project-1" />);

    expect(await screen.findByText("生产发布门禁")).toBeVisible();
    expect(screen.getByText(gate.rule_summary!)).toBeVisible();
    expect(screen.getByText("最近决策 failed")).toBeVisible();
    expect(screen.getByText("阻塞项 2")).toBeVisible();
    expect(screen.getByRole("link", { name: /RUN-PREVIOUS/ })).toHaveAttribute(
      "href",
      "/projects/project-1/runs/run-previous",
    );
    expect(screen.getByText(/真实运行结果做发布判断/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: /1. 配置测试计划/ }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
    expect(
      screen.getByRole("link", { name: /2. 查看运行结果/ }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(
      screen.getByRole("link", { name: /3. 补齐风险证据/ }),
    ).toHaveAttribute("href", "/projects/project-1/security");
    expect(screen.getByRole("link", { name: "查看安全发现" })).toHaveAttribute(
      "href",
      "/projects/project-1/security",
    );
    expect(screen.getByRole("link", { name: "处理人工审核" })).toHaveAttribute(
      "href",
      "/projects/project-1/reviews",
    );
    expect(screen.getByRole("link", { name: "查看实验对比" })).toHaveAttribute(
      "href",
      "/projects/project-1/experiments",
    );
    expect(
      document.querySelector('[role="tooltip"][data-tooltip="删除"]'),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("选择执行记录"), {
      target: { value: "run-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "评估运行结果" }));

    await waitFor(() =>
      expect(api.evaluateGate).toHaveBeenCalledWith("project-1", "gate-1", {
        run_id: "run-1",
      }),
    );
    expect(await screen.findByText("门禁通过")).toBeVisible();
  });

  it("guides empty gates to plans and runs", async () => {
    api.listGates.mockResolvedValue([]);
    api.listGatePage.mockResolvedValue([]);
    api.listGateRuns.mockResolvedValue([]);

    render(<GateList projectId="project-1" />);

    expect(await screen.findByText("暂无门禁")).toBeVisible();
    expect(screen.getByText(/测试计划版本里选择它/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: "去配置测试计划" }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
    expect(screen.getByRole("link", { name: "去运行中心" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs",
    );
  });
});
