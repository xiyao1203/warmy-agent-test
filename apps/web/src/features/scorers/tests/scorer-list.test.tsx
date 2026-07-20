import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ScorerList } from "../scorer-list";
import type { ScorerItem } from "../api";

const api = vi.hoisted(() => ({
  createScorer: vi.fn(),
  deleteScorer: vi.fn(),
  listScorers: vi.fn(),
  listScorerPage: vi.fn(),
  trialScorer: vi.fn(),
  updateScorer: vi.fn(),
}));

vi.mock("../api", () => api);

const scorer: ScorerItem = {
  config_json: { operator: "contains", expected: "ok" },
  created_at: "2026-07-01T10:00:00Z",
  description: "检查回答是否包含关键结果",
  enabled: true,
  id: "scorer-1",
  latest_published_version_id: "scorer-version-2",
  latest_published_version_number: 2,
  latest_version: {
    href: "/projects/project-1/scorers",
    id: "scorer-1",
    name: "事实评分",
    resource_type: "scorer",
    status: "published",
    version: 2,
  },
  last_calibrated_at: "2026-07-15T10:00:00Z",
  name: "事实评分",
  project_id: "project-1",
  scorer_type: "rule",
  threshold: 0.8,
  updated_at: "2026-07-01T10:00:00Z",
  usage_count: 24,
  weight: 1,
};

describe("ScorerList", () => {
  beforeEach(() => {
    api.createScorer.mockReset();
    api.deleteScorer.mockReset();
    api.listScorers.mockReset();
    api.listScorerPage.mockReset();
    api.trialScorer.mockReset();
    api.updateScorer.mockReset();
  });

  it("shows the scorer workflow and plan links", async () => {
    api.listScorers.mockResolvedValue([scorer]);
    api.listScorerPage.mockResolvedValue([scorer]);

    render(<ScorerList projectId="project-1" />);

    expect((await screen.findAllByText("事实评分")).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/测试计划选择后，运行结果会自动产出评分/),
    ).toBeVisible();
    expect(screen.getByText("1. 新建评分器")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /2. 配置测试计划/ }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
    expect(
      screen.getByRole("link", { name: /3. 查看评分结果/ }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(screen.getByRole("link", { name: /4. 做实验对比/ })).toHaveAttribute(
      "href",
      "/projects/project-1/experiments",
    );
    expect(screen.getByText("可用于计划 v2")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /事实评分.*v2.*published/ }),
    ).toHaveAttribute("href", "/projects/project-1/scorers");
    expect(screen.getByText("引用次数 24")).toBeVisible();
    expect(screen.getByRole("link", { name: "配置计划" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-plans",
    );
    expect(screen.getByRole("button", { name: "设置事实评分" })).toBeVisible();
    expect(
      document.querySelector('[role="tooltip"][data-tooltip="禁用"]'),
    ).toBeInTheDocument();
    expect(
      document.querySelector('[role="tooltip"][data-tooltip="设置"]'),
    ).toBeInTheDocument();
    expect(
      document.querySelector('[role="tooltip"][data-tooltip="删除"]'),
    ).toBeInTheDocument();
  });

  it("guides empty state to create scorer and configure plans", async () => {
    api.listScorers.mockResolvedValue([]);
    api.listScorerPage.mockResolvedValue([]);

    render(<ScorerList projectId="project-1" />);

    expect(await screen.findByText("暂无评分器")).toBeVisible();
    expect(screen.getByText(/测试计划的评估设置中选择它/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: "去配置测试计划" }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
  });
});
