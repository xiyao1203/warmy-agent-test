import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ReviewTask } from "../api";
import { ReviewWorkbench } from "../review-workbench";

const api = vi.hoisted(() => ({
  listReviews: vi.fn(),
  rejectReview: vi.fn(),
  scoreReview: vi.fn(),
  skipReview: vi.fn(),
}));

vi.mock("../api", () => api);

const task: ReviewTask = {
  age_seconds: 7200,
  assignee_ref: {
    href: null,
    id: "user-2",
    name: "高级测试工程师",
    resource_type: "user",
  },
  case_ref: {
    href: "/projects/project-1/datasets",
    id: "test-case-1",
    key: "PAY-TC-001",
    name: "支付异常恢复",
    resource_type: "test_case",
  },
  confidence: 0.42,
  created_at: "2026-07-04T10:00:00Z",
  id: "review-1",
  enqueue_reason: "low_confidence",
  opinion: null,
  project_id: "project-1",
  priority: 58,
  reviewer_id: null,
  reviewed_at: null,
  rubric_scores: null,
  run_case_id: "case-1234567890",
  run_ref: {
    href: "/projects/project-1/runs/run-1",
    id: "run-1",
    name: "RUN-0001",
    resource_type: "run",
  },
  score: null,
  status: "pending",
  updated_at: "2026-07-04T10:00:00Z",
};

describe("ReviewWorkbench", () => {
  beforeEach(() => {
    api.listReviews.mockReset();
    api.rejectReview.mockReset();
    api.scoreReview.mockReset();
    api.skipReview.mockReset();
  });

  it("shows where review tasks come from and where they go next", async () => {
    api.listReviews.mockResolvedValue([task]);

    render(<ReviewWorkbench projectId="project-1" />);

    expect(await screen.findByText("case-1234567")).toBeVisible();
    expect(screen.getByText(/优先级 58 · 等待 2 小时/)).toBeVisible();
    expect(screen.getByText(/低置信、高风险或评分冲突/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: /1. 运行产生任务/ }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(
      screen.getByRole("link", { name: /3. 查看安全测试/ }),
    ).toHaveAttribute("href", "/projects/project-1/security");
    expect(
      screen.getByRole("link", { name: /4. 发布门禁放行/ }),
    ).toHaveAttribute("href", "/projects/project-1/gates");

    fireEvent.click(screen.getByText("case-1234567"));
    expect(screen.getByRole("link", { name: /RUN-0001/ })).toHaveAttribute(
      "href",
      "/projects/project-1/runs/run-1",
    );
    expect(screen.getByRole("link", { name: /支付异常恢复/ })).toHaveAttribute(
      "href",
      "/projects/project-1/datasets",
    );
    expect(
      screen.getByText(/先回到运行中心核对输入、输出、Trace/),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "查看运行证据" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs",
    );
    expect(screen.getByRole("link", { name: "查看门禁影响" })).toHaveAttribute(
      "href",
      "/projects/project-1/gates",
    );
    expect(
      screen.getByRole("button", { name: /暂不处理 case-1234567/ }),
    ).toBeVisible();
  });

  it("guides empty review queue back to runs and gates", async () => {
    api.listReviews.mockResolvedValue([]);

    render(<ReviewWorkbench projectId="project-1" />);

    expect(await screen.findByText("暂无审核任务")).toBeVisible();
    expect(screen.getByText(/运行完成后，需要人工判断的用例/)).toBeVisible();
    expect(screen.getByRole("link", { name: "去运行中心" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs",
    );
    expect(screen.getByRole("link", { name: "查看发布门禁" })).toHaveAttribute(
      "href",
      "/projects/project-1/gates",
    );
  });
});
