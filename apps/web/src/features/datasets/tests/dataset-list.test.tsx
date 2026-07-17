import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects/project-1/datasets",
  useRouter: () => ({ replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

import { DatasetDetail } from "../dataset-detail";
import { DatasetList } from "../dataset-list";
import { TestCaseEditor } from "../test-case-editor";

const dataset = {
  api_count: 12,
  browser_count: 5,
  case_count: 20,
  codex_explore_count: 3,
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  description: "Agent 对话回归集",
  id: "dataset-1",
  latest_version: {
    href: "/projects/project-1/datasets/dataset-1",
    id: "dataset-version-3",
    name: "对话回归",
    resource_type: "dataset_version" as const,
    status: "published",
    version: 3,
  },
  name: "对话回归",
  project_id: "project-1",
  priority_coverage: { P0: 4, P1: 16 },
  ready_count: 18,
  source_distribution: { agent_generated: 8, manual: 12 },
  updated_at: "2026-06-25T10:00:00Z",
  updated_by: "user-1",
};

const draftVersion = {
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  dataset_id: dataset.id,
  id: "version-1",
  published_at: null,
  status: "draft" as const,
  updated_at: "2026-06-25T10:00:00Z",
  version_number: 1,
};

const testCase = {
  artifact_requirements: [],
  assertions: [{ type: "contains", value: "hello" }],
  automation_status: "automated" as const,
  case_key: "DEMO-TC-000001",
  case_status: "ready" as const,
  case_type: "smoke" as const,
  component: "对话",
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  custom_fields: {},
  data_bindings: [],
  dataset_version_id: draftVersion.id,
  difficulty: null,
  execution_mode: "api" as const,
  expected_outcome: { answer: "hello" },
  id: "case-1",
  initial_state: null,
  input: { message: "hi" },
  name: "基础问候",
  objective: "验证基础问候",
  owner_id: null,
  postconditions: [],
  preconditions: [],
  priority: "P0" as const,
  risk_level: "low" as const,
  scenario: null,
  scorers: [],
  security_policies: [],
  sort_order: 1,
  source: "manual" as const,
  source_ref: null,
  steps: [],
  tags: ["smoke"],
  template: "ai_eval" as const,
  test_group: "test" as const,
  timeout_seconds: null,
  estimated_duration_seconds: null,
  retry_count: 0,
  requirement_refs: [],
  updated_at: "2026-06-25T10:00:00Z",
  updated_by: "user-1",
};

describe("DatasetList", () => {
  it("renders loading, empty, error and populated states", () => {
    const { rerender } = render(<DatasetList loading projectId="project-1" />);
    expect(screen.getByText("正在加载用例集…")).toBeVisible();

    rerender(<DatasetList datasets={[]} projectId="project-1" />);
    expect(screen.getByText("暂无用例集")).toBeVisible();

    rerender(<DatasetList error="service" projectId="project-1" />);
    expect(screen.getByText("用例集列表暂时不可用")).toBeVisible();

    rerender(
      <DatasetList
        datasets={[dataset]}
        onDelete={vi.fn()}
        projectId="project-1"
      />,
    );
    expect(screen.getAllByText("对话回归").length).toBeGreaterThan(0);
    expect(screen.getByText("Agent 对话回归集")).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "用例集信息" }),
    ).toHaveClass("w-[25%]");
    expect(screen.getByRole("columnheader", { name: "更新时间" })).toHaveClass(
      "w-[12%]",
    );
    expect(
      screen.getByRole("columnheader", { name: "最新版本" }),
    ).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "用例覆盖" }),
    ).toBeVisible();
    expect(screen.getByText(/用例 20 · 就绪 18/)).toBeVisible();
    expect(screen.getByText(/优先级：P0 4 · P1 16/)).toBeVisible();
    expect(
      screen.getByText(/来源：agent_generated 8 · manual 12/),
    ).toBeVisible();
    expect(
      screen.getByRole("link", { name: /对话回归.*v3.*published/ }),
    ).toHaveAttribute("href", "/projects/project-1/datasets/dataset-1");
    expect(screen.getByRole("table")).toHaveClass("w-full", "table-fixed");
    expect(screen.getByRole("group", { name: "对话回归 操作" })).toHaveClass(
      "whitespace-nowrap",
    );
    expect(
      screen.getByRole("link", { name: "管理对话回归用例" }),
    ).toHaveAttribute("href", "/projects/project-1/datasets/dataset-1");
    expect(
      screen.queryByRole("link", { name: "查看对话回归" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "删除对话回归" })).toBeVisible();
  });

  it("creates a dataset", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(
      <DatasetList datasets={[]} onCreate={onCreate} projectId="project-1" />,
    );

    fireEvent.click(screen.getByRole("button", { name: "创建用例集" }));
    fireEvent.change(screen.getByLabelText("用例集名称"), {
      target: { value: "安全回归" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存用例集" }));

    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ name: "安全回归" }),
    );
  });
});

describe("DatasetDetail", () => {
  it("keeps the create case action visible when a case set has no version yet", () => {
    render(
      <DatasetDetail
        cases={[]}
        dataset={dataset}
        onCreateCase={vi.fn()}
        projectId="project-1"
        versions={[]}
      />,
    );

    expect(
      screen.getAllByRole("button", { name: "新增用例" }).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("暂无测试用例")).toBeVisible();
  });

  it("shows CRUD actions and a test plan link for draft versions", async () => {
    const onCreateCase = vi.fn().mockResolvedValue(undefined);
    const onDeleteCases = vi.fn().mockResolvedValue(undefined);
    const onUpdateCase = vi.fn().mockResolvedValue(undefined);
    render(
      <DatasetDetail
        cases={[testCase]}
        currentVersionId={draftVersion.id}
        dataset={dataset}
        onCreateCase={onCreateCase}
        onDeleteCases={onDeleteCases}
        onUpdateCase={onUpdateCase}
        projectId="project-1"
        versions={[draftVersion]}
      />,
    );

    expect(screen.getByText(dataset.name)).toBeVisible();
    expect(screen.getByText("基础问候")).toBeVisible();
    expect(screen.getByText("API")).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "步骤 / 断言" }),
    ).toBeVisible();
    expect(screen.getByText("1 条断言")).toBeVisible();
    expect(screen.getByRole("button", { name: "编辑基础问候" })).toHaveClass(
      "whitespace-nowrap",
    );
    expect(screen.getByRole("button", { name: "删除基础问候" })).toBeVisible();
    expect(
      screen.getByRole("link", { name: "用这些用例创建测试计划" }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");

    fireEvent.click(screen.getByRole("button", { name: "查看详情" }));
    expect(screen.getByText("断言规则")).toBeVisible();
    expect(screen.getByText(/contains/)).toBeVisible();
    fireEvent.click(screen.getAllByRole("button", { name: "关闭" })[1]);

    fireEvent.click(screen.getByRole("button", { name: "新增用例" }));
    expect(
      screen.getByRole("button", { name: "断言、评分与安全" }),
    ).toBeVisible();
    fireEvent.change(screen.getByLabelText("用例名称"), {
      target: { value: "新增问候" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存草稿" }));

    await waitFor(() => expect(onCreateCase).toHaveBeenCalledTimes(1));
    expect(onCreateCase).toHaveBeenCalledWith(
      expect.objectContaining({ name: "新增问候" }),
    );

    fireEvent.click(screen.getByRole("button", { name: "编辑基础问候" }));
    fireEvent.change(screen.getByLabelText("用例名称"), {
      target: { value: "基础问候更新" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存草稿" }));

    await waitFor(() => expect(onUpdateCase).toHaveBeenCalledTimes(1));
    expect(onUpdateCase).toHaveBeenCalledWith(
      "case-1",
      expect.objectContaining({ name: "基础问候更新" }),
    );

    fireEvent.click(screen.getByRole("button", { name: "删除基础问候" }));
    await waitFor(() => expect(onDeleteCases).toHaveBeenCalledWith(["case-1"]));
  });

  it("explains that published versions are read-only", () => {
    render(
      <DatasetDetail
        cases={[testCase]}
        currentVersionId={draftVersion.id}
        currentVersionPublished
        dataset={dataset}
        onCreateCase={vi.fn()}
        onUpdateCase={vi.fn()}
        projectId="project-1"
        versions={[{ ...draftVersion, status: "published" }]}
      />,
    );

    expect(screen.getByText("当前版本已发布，只读")).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "新增用例" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "编辑基础问候" }),
    ).not.toBeInTheDocument();
  });
});

describe("TestCaseEditor", () => {
  it("submits enhanced test case fields with API enum values", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TestCaseEditor onSubmit={onSubmit} triggerLabel="新增用例" />);

    fireEvent.click(screen.getByRole("button", { name: "新增用例" }));
    fireEvent.change(screen.getByLabelText("用例名称"), {
      target: { value: "权限回归" },
    });
    fireEvent.change(screen.getByLabelText("优先级"), {
      target: { value: "P1" },
    });
    fireEvent.change(screen.getByLabelText("风险等级"), {
      target: { value: "high" },
    });
    fireEvent.change(screen.getByLabelText("测试分组"), {
      target: { value: "validation" },
    });
    expect(
      screen.getByRole("button", { name: "断言、评分与安全" }),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "输入数据" }));
    expect(screen.queryByLabelText("输入 JSON")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "添加输入字段" }));
    fireEvent.change(screen.getByLabelText("输入数据字段名"), {
      target: { value: "message" },
    });
    fireEvent.change(screen.getByLabelText("输入数据字段值"), {
      target: { value: "你好" },
    });
    fireEvent.click(screen.getByRole("button", { name: "断言、评分与安全" }));
    fireEvent.click(screen.getByRole("button", { name: "添加断言" }));
    fireEvent.change(screen.getByLabelText("断言字段"), {
      target: { value: "output.text" },
    });
    fireEvent.change(screen.getByLabelText("断言期望值"), {
      target: { value: "你好" },
    });
    expect(screen.queryByLabelText("评分器配置")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "添加评分器" }));
    fireEvent.change(screen.getByLabelText("评分器名称"), {
      target: { value: "helpfulness" },
    });
    fireEvent.click(screen.getByRole("button", { name: "添加安全策略" }));
    fireEvent.change(screen.getByLabelText("安全策略类型"), {
      target: { value: "pii_redaction" },
    });
    fireEvent.click(screen.getByRole("button", { name: "收尾与执行" }));
    fireEvent.change(screen.getByLabelText("执行模式"), {
      target: { value: "codex_explore" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存草稿" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        assertions: [expect.objectContaining({ path: "output.text" })],
        execution_mode: "codex_explore",
        input: { message: "你好" },
        name: "权限回归",
        priority: "P1",
        risk_level: "high",
        scorers: [expect.objectContaining({ name: "helpfulness" })],
        security_policies: [expect.objectContaining({ type: "pii_redaction" })],
        test_group: "validation",
      }),
    );
  });
});
