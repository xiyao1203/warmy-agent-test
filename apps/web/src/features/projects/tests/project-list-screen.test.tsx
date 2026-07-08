import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProjectListScreen } from "../project-list-screen";

const projects = [
  { archived: false, id: "project-1", name: "项目 A" },
  { archived: true, id: "project-2", name: "项目 B" },
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

    expect(screen.getByRole("heading", { name: "项目管理" })).toBeVisible();
    expect(screen.getByTestId("project-filter-bar")).toHaveClass(
      "flex",
      "items-center",
      "gap-3",
    );
    expect(screen.getByRole("columnheader", { name: "项目" })).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "状态" })).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "默认入口" }),
    ).toBeVisible();
    expect(screen.getByText("项目 A")).toBeVisible();
    expect(screen.getByText("项目 B")).toBeVisible();
    expect(screen.getAllByText("已归档").length).toBeGreaterThan(0);

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

  it("renames a project inline", async () => {
    const handlers = renderProjectListScreen();
    render(<ProjectListScreen projects={projects} {...handlers} />);

    fireEvent.click(screen.getByRole("button", { name: "编辑项目 A" }));
    fireEvent.change(screen.getByDisplayValue("项目 A"), {
      target: { value: "项目 A 改名" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存项目 A" }));

    await waitFor(() =>
      expect(handlers.onRename).toHaveBeenCalledWith("project-1", {
        name: "项目 A 改名",
      }),
    );
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
