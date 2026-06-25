import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProjectSwitcher } from "../project-switcher";

describe("ProjectSwitcher", () => {
  it("shows only supplied authorized projects and filters them", () => {
    const onSelect = vi.fn();
    render(
      <ProjectSwitcher
        currentProjectId="project-a"
        onSelect={onSelect}
        projects={[
          { archived: false, id: "project-a", name: "项目 A" },
          { archived: true, id: "project-b", name: "项目 B" },
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
    expect(screen.queryByRole("option", { name: /项目 A/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("option", { name: /项目 B/ }));
    expect(onSelect).toHaveBeenCalledWith("project-b");
  });
});
