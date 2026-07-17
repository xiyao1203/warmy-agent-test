import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { projectFixture } from "@/test/fixtures";

import { ProjectSwitcher } from "../project-switcher";

describe("ProjectSwitcher", () => {
  it("shows only supplied authorized projects and filters them", () => {
    const onSelect = vi.fn();
    render(
      <ProjectSwitcher
        currentProjectId="project-a"
        onSelect={onSelect}
        projects={[
          projectFixture({ id: "project-a" }),
          projectFixture({
            archived: true,
            id: "project-b",
            key: "PRJ002",
            name: "项目 B",
            status: "archived",
          }),
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /项目 A/ }));
    expect(screen.getByRole("option", { name: /项目 A/ })).toBeVisible();
    expect(screen.getByRole("option", { name: /项目 B/ })).toBeVisible();
    expect(screen.queryByText("未授权项目")).not.toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("搜索项目"), {
      target: { value: "项目 B" },
    });
    expect(
      screen.queryByRole("option", { name: /项目 A/ }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("option", { name: /项目 B/ }));
    expect(onSelect).toHaveBeenCalledWith("project-b");
  });
});
