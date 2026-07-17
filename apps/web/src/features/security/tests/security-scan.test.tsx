import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SecurityScanItem, SecurityTarget } from "../api";
import { SecurityScanPage } from "../security-scan";

const api = vi.hoisted(() => ({
  listScans: vi.fn(),
  listSecurityTargets: vi.fn(),
  triggerScan: vi.fn(),
}));

vi.mock("../api", () => api);

const target: SecurityTarget = {
  id: "agent-version-1",
  label: "客服 Agent · v2",
};

const scan: SecurityScanItem = {
  agent_ref: {
    href: "/projects/project-1/agents/agent-1",
    id: "agent-version-1",
    name: "客服 Agent",
    resource_type: "agent_version",
    version: 2,
  },
  agent_version_id: "agent-version-1",
  completed_at: "2026-07-04T10:10:00Z",
  created_at: "2026-07-04T10:00:00Z",
  critical_count: 1,
  duration_ms: 600000,
  environment_version_id: null,
  findings: [
    {
      category: "injection",
      description: "模型接受了不可信指令",
      response: "unsafe",
      score: 0.3,
      severity: "high",
      title: "Prompt 注入风险",
      vector: "ignore previous instructions",
    },
  ],
  id: "scan-1234567890",
  high_count: 2,
  low_count: 4,
  medium_count: 3,
  profile_ref: {
    href: "/projects/project-1/security",
    id: "security-profile-1",
    name: "OWASP LLM",
    resource_type: "security_profile",
  },
  project_id: "project-1",
  run_id: "run-1",
  run_ref: {
    href: "/projects/project-1/runs/run-1",
    id: "run-1",
    name: "RUN-0001",
    resource_type: "run",
  },
  scan_type: "full",
  security_profile_id: null,
  status: "completed",
  started_at: "2026-07-04T10:00:00Z",
  summary: { injection: 1, jailbreak: 0, leak: 0, score: 0.72 },
  updated_at: "2026-07-04T10:10:00Z",
};

describe("SecurityScanPage", () => {
  beforeEach(() => {
    api.listScans.mockReset();
    api.listSecurityTargets.mockReset();
    api.triggerScan.mockReset();
  });

  it("shows the security workflow and gate links", async () => {
    api.listScans.mockResolvedValue([scan]);
    api.listSecurityTargets.mockResolvedValue([target]);

    render(<SecurityScanPage projectId="project-1" />);

    expect(await screen.findByText("scan-1234567")).toBeVisible();
    expect(screen.getByText(/严重 1 · 高 2 · 中 3 · 低 4/)).toBeVisible();
    expect(screen.getByText(/结果会进入发布门禁评估/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: /1. 选择 Agent 版本/ }),
    ).toHaveAttribute("href", "/projects/project-1/agents");
    expect(
      screen.getByRole("link", { name: /3. 查看运行证据/ }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(
      screen.getByRole("link", { name: /4. 发布门禁判断/ }),
    ).toHaveAttribute("href", "/projects/project-1/gates");

    fireEvent.click(screen.getByText("scan-1234567"));
    expect(screen.getByRole("link", { name: /RUN-0001/ })).toHaveAttribute(
      "href",
      "/projects/project-1/runs/run-1",
    );
    expect(
      screen.getByText(/安全发现会作为同一次运行的门禁证据/),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "查看发布门禁" })).toHaveAttribute(
      "href",
      "/projects/project-1/gates",
    );
    expect(screen.getByRole("link", { name: "去人工审核" })).toHaveAttribute(
      "href",
      "/projects/project-1/reviews",
    );
  });

  it("guides empty scans to published agents and gates", async () => {
    api.listScans.mockResolvedValue([]);
    api.listSecurityTargets.mockResolvedValue([target]);

    render(<SecurityScanPage projectId="project-1" />);

    expect(await screen.findByText("暂无扫描记录")).toBeVisible();
    expect(screen.getByText(/先选择已发布 Agent 版本/)).toBeVisible();
    expect(screen.getByRole("button", { name: /启动安全测试/ })).toBeDisabled();
    expect(screen.getByRole("link", { name: "去发布 Agent" })).toHaveAttribute(
      "href",
      "/projects/project-1/agents",
    );
    expect(screen.getByRole("link", { name: "配置发布门禁" })).toHaveAttribute(
      "href",
      "/projects/project-1/gates",
    );
  });
});
