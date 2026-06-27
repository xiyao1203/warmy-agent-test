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

    rerender(
      <DatasetList
        datasets={[dataset]}
        onDelete={vi.fn()}
        projectId="project-1"
      />,
    );
    expect(screen.getByText("对话回归")).toBeVisible();
    expect(screen.getByText("Agent 对话回归集")).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "数据集信息" }),
    ).toHaveClass("w-[420px]", "pl-16");
    expect(screen.getByRole("columnheader", { name: "更新时间" })).toHaveClass(
      "w-32",
      "text-center",
    );
    expect(screen.getByRole("table")).toHaveClass("w-auto", "table-fixed");
    expect(screen.getByRole("group", { name: "对话回归 操作" })).toHaveClass(
      "whitespace-nowrap",
    );
    expect(screen.getByRole("link", { name: "查看对话回归" })).toHaveAttribute(
      "href",
      "/projects/project-1/datasets/dataset-1",
    );
    expect(screen.getByRole("button", { name: "删除对话回归" })).toBeVisible();
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
  it("shows cases and version badges", async () => {
    render(
      <DatasetDetail
        cases={[testCase]}
        currentVersionId={draftVersion.id}
        dataset={dataset}
        projectId="project-1"
        versions={[draftVersion]}
      />,
    );

    expect(screen.getByText(dataset.name)).toBeVisible();
    expect(screen.getByText("基础问候")).toBeVisible();
    expect(screen.getByText("API")).toBeVisible();
  });
});
