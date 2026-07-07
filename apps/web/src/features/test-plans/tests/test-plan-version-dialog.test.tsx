import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  TestPlanVersionDialog,
  type VersionAssetOption,
} from "../test-plan-version-dialog";

const agentVersions: VersionAssetOption[] = [
  { id: "agent-draft", label: "客服 Agent v1", status: "draft" },
  {
    id: "agent-published",
    label: "客服 Agent v2",
    status: "published",
  },
];
const datasetVersions: VersionAssetOption[] = [
  { id: "dataset-draft", label: "回归集 v1", status: "draft" },
  {
    id: "dataset-published",
    label: "回归集 v2",
    status: "published",
  },
];
const environments: VersionAssetOption[] = [
  { id: "environment-1", label: "浏览器沙箱" },
];
const scorers: VersionAssetOption[] = [{ id: "scorer-1", label: "事实准确性" }];

function renderDialog(
  overrides?: Partial<{
    version: Parameters<typeof TestPlanVersionDialog>[0]["version"];
  }>,
) {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  const view = render(
    <TestPlanVersionDialog
      agentVersions={agentVersions}
      datasetVersions={datasetVersions}
      environments={environments}
      gates={[]}
      planId="plan-1"
      projectId="project-1"
      runs={[]}
      scorers={scorers}
      onSubmit={onSubmit}
      triggerLabel="创建版本"
      version={overrides?.version}
    />,
  );
  return { ...view, onSubmit };
}

describe("TestPlanVersionDialog", () => {
  it("navigates through all four steps and submits", async () => {
    const { onSubmit } = renderDialog();
    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    // Step 1: 选择测试资产
    expect(screen.getByText("选择测试资产")).toBeVisible();
    expect(
      screen.queryByRole("option", { name: "客服 Agent v1" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("option", { name: "客服 Agent v2" })).toBeVisible();

    fireEvent.change(screen.getByLabelText("Agent 版本"), {
      target: { value: "agent-published" },
    });
    fireEvent.change(screen.getByLabelText("数据集版本"), {
      target: { value: "dataset-published" },
    });
    fireEvent.change(screen.getByLabelText("环境模板"), {
      target: { value: "environment-1" },
    });
    expect(screen.getByText(/发布环境版本后/)).toBeVisible();
    expect(screen.getByRole("link", { name: "去管理环境" })).toHaveAttribute(
      "href",
      "/projects/project-1/environments",
    );

    // Step 1 -> 2
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    expect(screen.getByText("执行配置")).toBeVisible();
    expect(screen.getByText(/浏览器用例运行时会复用选中实例/)).toBeVisible();
    expect(screen.getByText(/默认使用运行机器上的 Codex CLI/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: "去管理浏览器实例" }),
    ).toHaveAttribute("href", "/projects/project-1/browser-profiles");

    // Step 2 -> 3
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    expect(screen.getByText("评估设置")).toBeVisible();
    expect(screen.getByText(/运行完成后会生成评分结果/)).toBeVisible();
    expect(screen.getByRole("link", { name: "去管理评分器" })).toHaveAttribute(
      "href",
      "/projects/project-1/scorers",
    );
    expect(screen.getByRole("link", { name: "去实验对比" })).toHaveAttribute(
      "href",
      "/projects/project-1/experiments",
    );

    // Step 3 -> 4
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    expect(screen.getByText("门禁配置")).toBeVisible();
    expect(screen.getByText(/门禁会读取测试执行的通过率/)).toBeVisible();
    expect(screen.getByRole("link", { name: "去安全测试" })).toHaveAttribute(
      "href",
      "/projects/project-1/security",
    );
    expect(screen.getByRole("link", { name: "去人工审核" })).toHaveAttribute(
      "href",
      "/projects/project-1/reviews",
    );
    expect(screen.getByRole("link", { name: "去发布门禁" })).toHaveAttribute(
      "href",
      "/projects/project-1/gates",
    );

    // Submit
    fireEvent.click(screen.getByRole("button", { name: "保存版本" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        agent_version_id: "agent-published",
        dataset_version_id: "dataset-published",
        environment_template_id: "environment-1",
        config: expect.objectContaining({
          concurrency: 1,
          timeout: 300,
          runs_per_case: 1,
        }),
      }),
    );
  });

  it("filters draft assets from selection", () => {
    renderDialog();
    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    // Draft agent should NOT be in the dropdown
    expect(
      screen.queryByRole("option", { name: "客服 Agent v1" }),
    ).not.toBeInTheDocument();
    // Published agent should be
    expect(screen.getByRole("option", { name: "客服 Agent v2" })).toBeVisible();
  });

  it("navigates back with 上一步 button", () => {
    renderDialog();
    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    // Go forward to step 3
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    expect(screen.getByText("评估设置")).toBeVisible();

    // Go back to step 2
    fireEvent.click(screen.getByRole("button", { name: "上一步" }));
    expect(screen.getByText("执行配置")).toBeVisible();

    // Go back to step 1
    fireEvent.click(screen.getByRole("button", { name: "上一步" }));
    expect(screen.getByText("选择测试资产")).toBeVisible();
  });

  it("shows observation mode checkbox in step 3", () => {
    renderDialog();
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

  it("submits custom Codex execution model from execution step", async () => {
    const { onSubmit } = renderDialog();
    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    fireEvent.change(screen.getByLabelText("Codex 执行模型"), {
      target: { value: "custom" },
    });
    fireEvent.change(screen.getByLabelText("Codex Provider ID"), {
      target: { value: "ollama" },
    });
    fireEvent.change(screen.getByLabelText("Codex 模型 ID"), {
      target: { value: "gpt-oss-120b" },
    });

    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    fireEvent.click(screen.getByRole("button", { name: "保存版本" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        config: expect.objectContaining({
          codex_model_provider: "ollama",
          codex_model: "gpt-oss-120b",
        }),
      }),
    );
  });

  it("shows step indicator with correct active state", () => {
    renderDialog();
    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    // Step labels visible
    expect(screen.getByText("选择测试资产")).toBeVisible();
    expect(screen.getByText("执行配置")).toBeVisible();
    expect(screen.getByText("评估设置")).toBeVisible();
    expect(screen.getByText("门禁配置")).toBeVisible();
  });

  it("pre-fills form fields from existing version", () => {
    const existingVersion = {
      agent_version_id: "agent-published",
      config: {
        codex_model: "gpt-5.5",
        codex_model_provider: "openai-compatible",
        concurrency: 3,
        cost_budget: 500,
        max_retries: 2,
        observation_only: true,
        pass_threshold: 0.85,
        runs_per_case: 5,
        timeout: 600,
      },
      created_at: "2026-06-25T10:00:00Z",
      created_by: "user-1",
      dataset_version_id: "dataset-published",
      environment_template_id: "environment-1",
      id: "version-1",
      published_at: null,
      status: "draft" as const,
      test_plan_id: "plan-1",
      updated_at: "2026-06-25T10:00:00Z",
      version_number: 1,
    };

    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <TestPlanVersionDialog
        agentVersions={agentVersions}
        datasetVersions={datasetVersions}
        environments={environments}
        gates={[]}
        planId="plan-1"
        projectId="project-1"
        runs={[]}
        scorers={scorers}
        onSubmit={onSubmit}
        triggerLabel={`编辑版本 v${existingVersion.version_number}`}
        version={existingVersion}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: `编辑版本 v${existingVersion.version_number}`,
      }),
    );

    // Step 1 - pre-filled selects
    expect(
      (screen.getByLabelText("Agent 版本") as HTMLSelectElement).value,
    ).toBe("agent-published");
    expect(
      (screen.getByLabelText("数据集版本") as HTMLSelectElement).value,
    ).toBe("dataset-published");
    expect((screen.getByLabelText("环境模板") as HTMLSelectElement).value).toBe(
      "environment-1",
    );

    // Step 2 - pre-filled numbers
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    expect((screen.getByLabelText("并发数") as HTMLInputElement).value).toBe(
      "3",
    );
    expect(
      (screen.getByLabelText("超时（秒）") as HTMLInputElement).value,
    ).toBe("600");
    expect(
      (screen.getByLabelText("最大重试次数") as HTMLInputElement).value,
    ).toBe("2");
    expect(
      (screen.getByLabelText("Codex 执行模型") as HTMLSelectElement).value,
    ).toBe("custom");
    expect(
      (screen.getByLabelText("Codex Provider ID") as HTMLInputElement).value,
    ).toBe("openai-compatible");
    expect(
      (screen.getByLabelText("Codex 模型 ID") as HTMLInputElement).value,
    ).toBe("gpt-5.5");
  });

  it("disables save button when readiness check returns not-ready", async () => {
    // Mock readiness as not-ready
    const existingVersion = {
      agent_version_id: null,
      config: {},
      created_at: "2026-06-25T10:00:00Z",
      created_by: "user-1",
      dataset_version_id: null,
      environment_template_id: null,
      id: "version-1",
      published_at: null,
      status: "draft" as const,
      test_plan_id: "plan-1",
      updated_at: "2026-06-25T10:00:00Z",
      version_number: 1,
    };

    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <TestPlanVersionDialog
        agentVersions={agentVersions}
        datasetVersions={datasetVersions}
        environments={environments}
        gates={[]}
        planId="plan-1"
        projectId="project-1"
        runs={[]}
        scorers={scorers}
        onSubmit={onSubmit}
        triggerLabel={`编辑版本 v${existingVersion.version_number}`}
        version={existingVersion}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: `编辑版本 v${existingVersion.version_number}`,
      }),
    );

    // Go to Step 4
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));

    // Readiness section should be visible
    expect(screen.getByText("资产就绪检查")).toBeVisible();
  });
});
