import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TestPlanDetail } from "../test-plan-detail";
import { TestPlanList } from "../test-plan-list";

const plan = {
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  description: "发布门禁",
  id: "plan-1",
  name: "回归计划",
  project_id: "project-1",
  updated_at: "2026-06-25T10:00:00Z",
  updated_by: "user-1",
};

const draftVersion = {
  agent_version_id: null,
  config: {
    concurrency: 2,
    pass_threshold: 0.9,
    runs_per_case: 1,
    timeout: 120,
  },
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  dataset_version_id: null,
  environment_template_id: null,
  id: "plan-version-1",
  published_at: null,
  status: "draft" as const,
  test_plan_id: plan.id,
  updated_at: "2026-06-25T10:00:00Z",
  version_number: 1,
};

const agentVersions = [
  { id: "agent-draft", label: "客服 Agent v1", status: "draft" as const },
  {
    id: "agent-published",
    label: "客服 Agent v2",
    status: "published" as const,
  },
];
const datasetVersions = [
  { id: "dataset-draft", label: "回归集 v1", status: "draft" as const },
  {
    id: "dataset-published",
    label: "回归集 v2",
    status: "published" as const,
  },
];
const environments = [{ id: "environment-1", label: "浏览器沙箱" }];

describe("TestPlanList", () => {
  it("renders loading, empty, error and populated states", () => {
    const { rerender } = render(<TestPlanList loading projectId="project-1" />);
    expect(screen.getByText("正在加载测试计划…")).toBeVisible();

    rerender(<TestPlanList plans={[]} projectId="project-1" />);
    expect(screen.getByText("暂无测试计划")).toBeVisible();

    rerender(<TestPlanList error="service" projectId="project-1" />);
    expect(screen.getByText("测试计划列表暂时不可用")).toBeVisible();

    rerender(
      <TestPlanList onDelete={vi.fn()} plans={[plan]} projectId="project-1" />,
    );
    expect(screen.getByText("回归计划")).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "计划信息" })).toHaveClass(
      "w-[420px]",
      "pl-16",
    );
    expect(screen.getByRole("columnheader", { name: "更新时间" })).toHaveClass(
      "w-32",
      "text-center",
    );
    expect(screen.getByRole("table")).toHaveClass("w-auto", "table-fixed");
    expect(screen.getByRole("group", { name: "回归计划 操作" })).toHaveClass(
      "whitespace-nowrap",
    );
    expect(screen.getByRole("link", { name: "查看回归计划" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-plans/plan-1",
    );
    expect(screen.getByRole("button", { name: "删除回归计划" })).toBeVisible();
  });

  it("creates a test plan", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(
      <TestPlanList plans={[]} onCreate={onCreate} projectId="project-1" />,
    );
    fireEvent.click(screen.getByRole("button", { name: "创建测试计划" }));
    fireEvent.change(screen.getByLabelText("计划名称"), {
      target: { value: "安全门禁" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存测试计划" }));
    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
  });
});

describe("TestPlanDetail", () => {
  it("creates a configured version using only published assets", async () => {
    const onCreateVersion = vi.fn().mockResolvedValue(undefined);
    render(
      <TestPlanDetail
        agentVersions={agentVersions}
        datasetVersions={datasetVersions}
        environments={environments}
        onCreateVersion={onCreateVersion}
        plan={plan}
        versions={[draftVersion]}
      />,
    );

    expect(screen.getByText("版本 v1")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    expect(
      screen.queryByRole("option", { name: "客服 Agent v1" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("option", { name: "客服 Agent v2" })).toBeVisible();
    expect(
      screen.queryByRole("option", { name: "回归集 v1" }),
    ).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Agent 版本"), {
      target: { value: "agent-published" },
    });
    fireEvent.change(screen.getByLabelText("数据集版本"), {
      target: { value: "dataset-published" },
    });
    fireEvent.change(screen.getByLabelText("环境模板"), {
      target: { value: "environment-1" },
    });
    fireEvent.change(screen.getByLabelText("并发数"), {
      target: { value: "4" },
    });
    fireEvent.change(screen.getByLabelText("超时（秒）"), {
      target: { value: "180" },
    });
    fireEvent.change(screen.getByLabelText("每条用例运行次数"), {
      target: { value: "2" },
    });
    fireEvent.change(screen.getByLabelText("通过阈值"), {
      target: { value: "0.95" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存版本" }));

    await waitFor(() => expect(onCreateVersion).toHaveBeenCalledTimes(1));
    expect(onCreateVersion).toHaveBeenCalledWith(
      expect.objectContaining({
        agent_version_id: "agent-published",
        dataset_version_id: "dataset-published",
        environment_template_id: "environment-1",
        config: expect.objectContaining({
          concurrency: 4,
          pass_threshold: 0.95,
          runs_per_case: 2,
          timeout: 180,
        }),
      }),
    );
  });

  it("publishes drafts and renders published versions read-only", async () => {
    const onPublish = vi.fn().mockResolvedValue(undefined);
    const { rerender } = render(
      <TestPlanDetail
        agentVersions={agentVersions}
        datasetVersions={datasetVersions}
        environments={environments}
        onPublish={onPublish}
        plan={plan}
        versions={[draftVersion]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "发布版本 v1" }));
    expect(await screen.findByText("发布后计划版本将不可编辑。")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "确认发布" }));
    await waitFor(() =>
      expect(onPublish).toHaveBeenCalledWith(draftVersion.id),
    );

    rerender(
      <TestPlanDetail
        agentVersions={agentVersions}
        datasetVersions={datasetVersions}
        environments={environments}
        plan={plan}
        versions={[
          {
            ...draftVersion,
            published_at: "2026-06-25T11:00:00Z",
            status: "published",
          },
        ]}
      />,
    );
    expect(screen.getByText("已锁定")).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "编辑版本 v1" }),
    ).not.toBeInTheDocument();
  });
});
