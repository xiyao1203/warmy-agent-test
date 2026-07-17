import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TestPlanDetail } from "../test-plan-detail";
import { TestPlanList } from "../test-plan-list";

const plan = {
  agent_ref: {
    href: "/projects/project-1/agents/agent-1",
    id: "agent-version-2",
    name: "客服 Agent",
    resource_type: "agent_version" as const,
    version: 2,
  },
  case_count: 48,
  concurrency: 4,
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  description: "发布门禁",
  id: "plan-1",
  dataset_ref: {
    href: "/projects/project-1/datasets/dataset-1",
    id: "dataset-version-3",
    name: "对话回归",
    resource_type: "dataset_version" as const,
    version: 3,
  },
  environment_ref: {
    href: "/projects/project-1/environments",
    id: "environment-1",
    name: "预发环境",
    resource_type: "environment" as const,
  },
  last_run_status: "passed",
  latest_version: {
    href: "/projects/project-1/test-plans/plan-1",
    id: "plan-version-4",
    name: "回归计划",
    resource_type: "test_plan_version" as const,
    status: "published",
    version: 4,
  },
  name: "回归计划",
  project_id: "project-1",
  pass_rate: 0.96,
  repeat_count: 2,
  retry_count: 1,
  scorer_count: 3,
  timeout_seconds: 120,
  updated_at: "2026-06-25T10:00:00Z",
  updated_by: "user-1",
};

const draftVersion = {
  agent_version_id: null,
  config: {
    concurrency: 2,
    codex_model: "gpt-5.5",
    codex_model_provider: "openai-compatible",
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
    expect(screen.getByRole("link", { name: "去准备用例集" })).toHaveAttribute(
      "href",
      "/projects/project-1/datasets",
    );

    rerender(<TestPlanList error="service" projectId="project-1" />);
    expect(screen.getByText("测试计划列表暂时不可用")).toBeVisible();

    rerender(
      <TestPlanList onDelete={vi.fn()} plans={[plan]} projectId="project-1" />,
    );
    expect(screen.getAllByText("回归计划").length).toBeGreaterThan(0);
    expect(screen.getByRole("columnheader", { name: "计划信息" })).toHaveClass(
      "w-[20%]",
    );
    expect(
      screen.getByRole("columnheader", { name: "资产绑定" }),
    ).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "执行配置" }),
    ).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "版本与结果" }),
    ).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "下一步" })).toHaveClass(
      "w-[13%]",
      "whitespace-nowrap",
    );
    expect(screen.getByText(/用例 48 · 重复 2 · 并发 4/)).toBeVisible();
    expect(screen.getByText(/超时 120 秒 · 重试 1 · 评分器 3/)).toBeVisible();
    expect(screen.getByText(/通过率 96.0%/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: /客服 Agent.*v2/ }),
    ).toHaveAttribute("href", "/projects/project-1/agents/agent-1");
    expect(screen.getByRole("table")).toHaveClass("w-full", "table-fixed");
    expect(screen.getByRole("group", { name: "回归计划 操作" })).toHaveClass(
      "whitespace-nowrap",
    );
    expect(
      screen.getByRole("link", { name: /选择待测 Agent/ }),
    ).toHaveAttribute("href", "/projects/project-1/agents");
    expect(screen.getByRole("link", { name: /准备用例集/ })).toHaveAttribute(
      "href",
      "/projects/project-1/datasets",
    );
    expect(screen.getByRole("link", { name: /查看测试执行/ })).toHaveAttribute(
      "href",
      "/projects/project-1/runs",
    );
    expect(screen.getByRole("link", { name: "配置回归计划" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-plans/plan-1",
    );
    expect(
      screen.queryByRole("link", { name: "查看回归计划" }),
    ).not.toBeInTheDocument();
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
  it("creates a configured version using four-step wizard", async () => {
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
    expect(
      screen.getByText(/Codex openai-compatible \/ gpt-5.5/),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    // Step 1: 选择测试资产
    expect(screen.getByText("选择测试资产")).toBeVisible();
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

    // Step 1 -> Step 2
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));

    // Step 2: 执行配置
    expect(screen.getByText("执行配置")).toBeVisible();
    fireEvent.change(screen.getByLabelText("并发数"), {
      target: { value: "4" },
    });
    fireEvent.change(screen.getByLabelText("超时（秒）"), {
      target: { value: "180" },
    });
    fireEvent.change(screen.getByLabelText("每条用例运行次数"), {
      target: { value: "2" },
    });

    // Step 2 -> Step 3
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));

    // Step 3: 评估设置
    expect(screen.getByText("评估设置")).toBeVisible();
    fireEvent.change(screen.getByLabelText("通过阈值"), {
      target: { value: "0.95" },
    });

    // Step 3 -> Step 4
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));

    // Step 4: 门禁配置
    expect(screen.getByText("门禁配置")).toBeVisible();
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

  it("navigates back and forth between steps", async () => {
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

    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    // Go to Step 2
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    expect(screen.getByText("执行配置")).toBeVisible();

    // Back to Step 1
    fireEvent.click(screen.getByRole("button", { name: "上一步" }));
    expect(screen.getByText("选择测试资产")).toBeVisible();
  });

  it("toggles observation mode in step 3", async () => {
    render(
      <TestPlanDetail
        agentVersions={agentVersions}
        datasetVersions={datasetVersions}
        environments={environments}
        plan={plan}
        versions={[draftVersion]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));
    // Advance to Step 3
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));

    expect(
      screen.getByRole("checkbox", {
        name: "仅观察模式（不配置评分器时必须显式开启）",
      }),
    ).toBeVisible();
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
