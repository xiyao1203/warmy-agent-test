import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./app-shell";

const project = { archived: false, id: "project-1", name: "项目 A" };

describe("AppShell", () => {
  it("hides system administration from ordinary users", () => {
    render(
      <AppShell
        currentProjectId={project.id}
        onProjectSelect={vi.fn()}
        projects={[project]}
        user={{
          display_name: "开发用户",
          email: "dev@example.com",
          id: "user-1",
          must_change_password: false,
          role: "developer",
          status: "active",
        }}
      >
        <div>Content</div>
      </AppShell>,
    );

    expect(screen.getByText("Warmy Agent Test")).toBeInTheDocument();
    expect(screen.getByText("项目概览")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Agent 与版本" })).toHaveAttribute(
      "href",
      "/projects/project-1/agents",
    );
    expect(screen.getByRole("link", { name: "数据集与用例" })).toHaveAttribute(
      "href",
      "/projects/project-1/datasets",
    );
    expect(screen.getByRole("link", { name: "测试计划" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-plans",
    );
    expect(screen.queryByText("系统管理")).not.toBeInTheDocument();
    expect(screen.queryByText("用户管理")).not.toBeInTheDocument();
  });

  it("shows system administration to super administrators", () => {
    render(
      <AppShell
        currentProjectId={project.id}
        onProjectSelect={vi.fn()}
        projects={[project]}
        user={{
          display_name: "系统管理员",
          email: "admin@example.com",
          id: "admin-1",
          must_change_password: false,
          role: "super_admin",
          status: "active",
        }}
      >
        <div>Content</div>
      </AppShell>,
    );

    expect(screen.getByText("系统管理")).toBeInTheDocument();
    expect(screen.getByText("用户管理")).toBeInTheDocument();
  });
});
