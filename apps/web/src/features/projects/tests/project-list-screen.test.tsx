import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { projectFixture } from "@/test/fixtures";

import { ProjectListScreen } from "../project-list-screen";

const projects = [
  projectFixture({
    agent_count: 2,
    dataset_count: 3,
    last_run: {
      href: "/projects/project-1/runs/run-42",
      id: "run-42",
      name: "RUN-0042",
      resource_type: "run",
      status: "passed",
    },
    last_run_at: "2026-07-16T08:00:00Z",
    member_count: 4,
    open_review_count: 1,
    test_case_count: 48,
    test_plan_count: 5,
  }),
  projectFixture({
    archived: true,
    id: "project-2",
    key: "PRJ002",
    name: "项目 B",
    status: "archived",
  }),
];

function renderProjectListScreen() {
  return {
    onArchive: vi.fn().mockResolvedValue(undefined),
    onCreate: vi.fn().mockResolvedValue(undefined),
    onOpen: vi.fn(),
    onRename: vi.fn().mockResolvedValue(undefined),
  };
}

describe("ProjectListScreen", () => {
  it("shows projects and opens the test agent from a row action", () => {
    const handlers = renderProjectListScreen();
    render(<ProjectListScreen projects={projects} {...handlers} />);

    expect(screen.getByRole("heading", { name: "项目管理" })).toHaveAttribute(
      "data-font-role",
      "display",
    );
    expect(screen.getByTestId("project-filter-bar")).toHaveClass(
      "flex",
      "items-center",
      "gap-3",
    );
    expect(screen.getByRole("columnheader", { name: "项目" })).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "状态" })).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "资产概览" }),
    ).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "最近运行" }),
    ).toBeVisible();
    expect(screen.getByText("项目 A")).toBeVisible();
    expect(screen.getByText("项目 B")).toBeVisible();
    expect(screen.getAllByText("已归档").length).toBeGreaterThan(0);
    expect(screen.getByText(/成员 4 · Agent 2 · 用例集 3/)).toBeVisible();
    expect(screen.getByRole("link", { name: /RUN-0042/ })).toHaveAttribute(
      "href",
      "/projects/project-1/runs/run-42",
    );
    expect(screen.getByTestId("project-summary-total")).toHaveAttribute(
      "data-font-role",
      "display-number",
    );

    fireEvent.click(
      screen.getByRole("button", { name: "进入项目 A 测试 Agent" }),
    );

    expect(handlers.onOpen).toHaveBeenCalledWith("project-1");
  });

  it("creates a project from the list page", async () => {
    const handlers = renderProjectListScreen();
    render(<ProjectListScreen projects={projects} {...handlers} />);

    expect(screen.queryByLabelText("项目名称")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "新建项目" }));
    fireEvent.change(screen.getByLabelText("项目名称"), {
      target: { value: "项目 C" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存项目" }));

    await waitFor(() =>
      expect(handlers.onCreate).toHaveBeenCalledWith({ name: "项目 C" }),
    );
  });

  it("uses the restrained product glyph for the empty state", () => {
    const handlers = renderProjectListScreen();
    render(<ProjectListScreen projects={[]} {...handlers} />);

    const visual = screen.getByTestId("project-empty-visual");

    expect(visual).toHaveAttribute(
      "data-visual-source",
      "warmy-product-system",
    );
    expect(visual).toHaveAttribute("data-visual-kind", "project-empty-glyph");
    expect(screen.getByText("暂无项目")).toBeVisible();
  });

  it("uses the shared loading cue while projects are loading", () => {
    const handlers = renderProjectListScreen();
    render(<ProjectListScreen loading projects={[]} {...handlers} />);

    const loader = screen.getByTestId("project-loading-motion");

    expect(loader).toHaveAttribute(
      "data-motion-source",
      "warmy-product-system",
    );
    expect(loader).toHaveTextContent("正在加载项目");
  });

  it("filters projects by keyword and status", () => {
    const handlers = renderProjectListScreen();
    render(<ProjectListScreen projects={projects} {...handlers} />);

    fireEvent.change(screen.getByPlaceholderText("搜索项目名称或 ID"), {
      target: { value: "project-2" },
    });

    expect(screen.queryByText("项目 A")).not.toBeInTheDocument();
    expect(screen.getByText("项目 B")).toBeVisible();

    fireEvent.change(screen.getByPlaceholderText("搜索项目名称或 ID"), {
      target: { value: "" },
    });
    fireEvent.change(screen.getByLabelText("按项目状态筛选"), {
      target: { value: "active" },
    });

    expect(screen.getByText("项目 A")).toBeVisible();
    expect(screen.queryByText("项目 B")).not.toBeInTheDocument();
  });

  it("renames a project from a dialog without expanding the table row", async () => {
    const handlers = renderProjectListScreen();
    render(<ProjectListScreen projects={projects} {...handlers} />);

    fireEvent.click(screen.getByRole("button", { name: "编辑项目 A" }));

    expect(screen.getByRole("heading", { name: "编辑项目" })).toBeVisible();
    fireEvent.change(screen.getByDisplayValue("项目 A"), {
      target: { value: "项目 A 改名" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存修改" }));

    await waitFor(() =>
      expect(handlers.onRename).toHaveBeenCalledWith("project-1", {
        name: "项目 A 改名",
      }),
    );
  });

  it("uses truncated full-text fields and compact icon-only row actions", () => {
    const handlers = renderProjectListScreen();
    const longName = "这是一个非常长的项目名称用于验证省略和完整文本提示";
    render(
      <ProjectListScreen
        projects={[projectFixture({ id: "project-long-id", name: longName })]}
        {...handlers}
      />,
    );

    expect(screen.getByLabelText(longName)).toHaveClass("truncate");
    expect(screen.getByLabelText("project-long-id")).toHaveClass("truncate");

    for (const label of [
      `进入${longName} 测试 Agent`,
      `编辑${longName}`,
      `归档${longName}`,
    ]) {
      const button = screen.getByRole("button", { name: label });
      expect(button).toHaveClass("size-8", "p-0");
      expect(button).not.toHaveTextContent(/进入|编辑|归档/);
    }
  });

  it("archives an active project", async () => {
    const handlers = renderProjectListScreen();
    render(<ProjectListScreen projects={projects} {...handlers} />);

    fireEvent.click(screen.getByRole("button", { name: "归档项目 A" }));

    await waitFor(() =>
      expect(handlers.onArchive).toHaveBeenCalledWith("project-1"),
    );
  });
});
