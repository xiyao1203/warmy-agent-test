import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppShell, initialSidebarCollapsed } from "./app-shell";

const project = { archived: false, id: "project-1", name: "项目 A" };

describe("AppShell", () => {
  beforeEach(() => {
    localStorage.clear();
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1024,
      writable: true,
    });
  });

  it("starts collapsed on narrow screens regardless of desktop preference", () => {
    expect(initialSidebarCollapsed(390, "false")).toBe(true);
    expect(initialSidebarCollapsed(1024, "false")).toBe(false);
    expect(initialSidebarCollapsed(1024, "true")).toBe(true);
  });

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

    expect(screen.getByText("Agent Test")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Agent Test" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-agent",
    );
    expect(screen.getByText("项目导航")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "项目列表" })).toHaveAttribute(
      "href",
      "/projects",
    );
    expect(screen.getByRole("link", { name: "测试 Agent" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-agent",
    );
    expect(screen.getByRole("link", { name: "概览" })).toHaveAttribute(
      "href",
      "/projects/project-1/overview",
    );
    expect(screen.getByRole("link", { name: "智能体" })).toHaveAttribute(
      "href",
      "/projects/project-1/agents",
    );
    expect(screen.getByRole("link", { name: "测试用例" })).toHaveAttribute(
      "href",
      "/projects/project-1/datasets",
    );
    expect(screen.getByRole("link", { name: "测试计划" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-plans",
    );
    const navLinks = screen
      .getAllByRole("link")
      .map((link) => link.textContent);
    expect(navLinks.indexOf("项目列表")).toBeLessThan(
      navLinks.indexOf("测试 Agent"),
    );
    expect(navLinks.indexOf("测试 Agent")).toBeLessThan(
      navLinks.indexOf("概览"),
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

  it("renders collapsed hover labels outside the scrollable navigation", () => {
    localStorage.setItem("sidebar-collapsed", "true");

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

    expect(screen.queryByText("项目导航")).not.toBeInTheDocument();
    fireEvent.mouseEnter(screen.getByTitle("测试 Agent"));

    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent("测试 Agent");
    expect(tooltip).toHaveClass("fixed");
    expect(
      screen.getByRole("navigation", { name: "项目导航" }),
    ).not.toContainElement(tooltip);
  });

  it("uses iconfont-inspired colorful SVG artworks matched to sidebar navigation semantics", () => {
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

    const expectedIcons = new Map<string, { icon: string; tone: string }>([
      ["项目列表", { icon: "project-list", tone: "indigo" }],
      ["测试 Agent", { icon: "test-agent", tone: "azure" }],
      ["概览", { icon: "overview", tone: "sky" }],
      ["智能体", { icon: "agent", tone: "violet" }],
      ["测试用例", { icon: "test-case", tone: "indigo" }],
      ["测试计划", { icon: "test-plan", tone: "amber" }],
      ["测试执行", { icon: "test-run", tone: "emerald" }],
      ["环境与凭证", { icon: "environment", tone: "teal" }],
      ["浏览器实例", { icon: "browser-profile", tone: "cyan" }],
      ["模型配置", { icon: "model", tone: "purple" }],
      ["评分器", { icon: "scorer", tone: "orange" }],
      ["实验对比", { icon: "experiment", tone: "fuchsia" }],
      ["人工审核", { icon: "review", tone: "rose" }],
      ["安全测试", { icon: "security", tone: "red" }],
      ["发布门禁", { icon: "release-gate", tone: "green" }],
      ["用户管理", { icon: "user-management", tone: "slate-blue" }],
    ]);

    for (const [label, expected] of expectedIcons) {
      const icon = screen
        .getByRole("link", { name: label })
        .querySelector("[data-sidebar-icon]");

      expect(icon).toHaveAttribute("data-sidebar-icon", expected.icon);
      expect(icon?.tagName.toLowerCase()).toBe("svg");
      expect(icon).toHaveAttribute("data-sidebar-icon-style", "iconfont-color");
      expect(icon).toHaveAttribute(
        "data-sidebar-icon-source",
        "iconfont-cn-inspired",
      );
      expect(icon).toHaveAttribute("data-sidebar-icon-tone", expected.tone);
      expect(icon?.querySelector("span")).toBeNull();
      expect(
        icon?.querySelectorAll("path, rect, circle, polygon"),
      ).toHaveLength(5);

      const style = icon?.getAttribute("style") ?? "";
      expect(style).toMatch(/--sidebar-icon-hot:\s*#[0-9a-f]{6}/i);
      expect(style).toMatch(/--sidebar-icon-cool:\s*#[0-9a-f]{6}/i);
      expect(style).toMatch(/--sidebar-icon-soft:\s*#[0-9a-f]{6}/i);
      expect(style).not.toContain("--sidebar-icon-primary");
      expect(style).not.toContain("--sidebar-icon-secondary");
      expect(style).not.toContain("--sidebar-icon-bg");
      expect(style).not.toContain("--sidebar-icon-dot");
    }
  });
});
