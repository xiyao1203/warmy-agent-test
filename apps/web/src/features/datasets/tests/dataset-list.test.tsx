import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DatasetDetail } from "../dataset-detail";
import { DatasetList } from "../dataset-list";

const dataset = {
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  description: "Agent 对话回归集",
  id: "dataset-1",
  name: "对话回归",
  project_id: "project-1",
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
  assertions: [{ type: "contains", value: "hello" }],
  created_at: "2026-06-25T10:00:00Z",
  dataset_version_id: draftVersion.id,
  difficulty: null,
  execution_mode: "api" as const,
  expected_outcome: { answer: "hello" },
  id: "case-1",
  initial_state: null,
  input: { message: "hi" },
  name: "基础问候",
  priority: "P0" as const,
  risk_level: "low" as const,
  scenario: null,
  scorers: [],
  security_policies: [],
  sort_order: 1,
  tags: ["smoke"],
  test_group: "test" as const,
  updated_at: "2026-06-25T10:00:00Z",
};

describe("DatasetList", () => {
  it("renders loading, empty, error and populated states", () => {
    const { rerender } = render(<DatasetList loading projectId="project-1" />);
    expect(screen.getByText("正在加载数据集…")).toBeVisible();

    rerender(<DatasetList datasets={[]} projectId="project-1" />);
    expect(screen.getByText("暂无数据集")).toBeVisible();

    rerender(<DatasetList error="service" projectId="project-1" />);
    expect(screen.getByText("数据集列表暂时不可用")).toBeVisible();

    rerender(<DatasetList datasets={[dataset]} projectId="project-1" />);
    expect(screen.getByText("对话回归")).toBeVisible();
    expect(screen.getByText("Agent 对话回归集")).toBeVisible();
  });

  it("creates a dataset", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(
      <DatasetList
        datasets={[]}
        onCreate={onCreate}
        projectId="project-1"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "创建数据集" }));
    fireEvent.change(screen.getByLabelText("数据集名称"), {
      target: { value: "安全回归" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存数据集" }));

    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ name: "安全回归" }),
    );
  });
});

describe("DatasetDetail", () => {
  it("switches versions, shows cases and creates a test case", async () => {
    const onCreateCase = vi.fn().mockResolvedValue(undefined);
    render(
      <DatasetDetail
        cases={testCase.dataset_version_id === draftVersion.id ? [testCase] : []}
        dataset={dataset}
        onCreateCase={onCreateCase}
        selectedVersionId={draftVersion.id}
        versions={[draftVersion]}
      />,
    );

    expect(screen.getByRole("tab", { name: "v1 草稿" })).toBeVisible();
    expect(screen.getByText("基础问候")).toBeVisible();
    expect(screen.getByText("API")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "添加用例" }));
    fireEvent.change(screen.getByLabelText("用例名称"), {
      target: { value: "流式回复" },
    });
    fireEvent.change(screen.getByLabelText("输入 JSON"), {
      target: { value: '{"message":"stream"}' },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存用例" }));

    await waitFor(() => expect(onCreateCase).toHaveBeenCalledTimes(1));
    expect(onCreateCase).toHaveBeenCalledWith(
      draftVersion.id,
      expect.objectContaining({
        execution_mode: "api",
        input: { message: "stream" },
        name: "流式回复",
      }),
    );
  });

  it("publishes a draft and renders published versions read-only", async () => {
    const onPublish = vi.fn().mockResolvedValue(undefined);
    const { rerender } = render(
      <DatasetDetail
        cases={[]}
        dataset={dataset}
        onPublish={onPublish}
        selectedVersionId={draftVersion.id}
        versions={[draftVersion]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "发布 v1" }));
    expect(await screen.findByText("发布后用例将不可编辑。")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "确认发布" }));
    await waitFor(() => expect(onPublish).toHaveBeenCalledWith(draftVersion.id));

    rerender(
      <DatasetDetail
        cases={[testCase]}
        dataset={dataset}
        selectedVersionId={draftVersion.id}
        versions={[
          {
            ...draftVersion,
            published_at: "2026-06-25T11:00:00Z",
            status: "published",
          },
        ]}
      />,
    );
    expect(screen.getByText("只读版本")).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "添加用例" }),
    ).not.toBeInTheDocument();
  });
});
