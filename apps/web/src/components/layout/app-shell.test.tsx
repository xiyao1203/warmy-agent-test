import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { projectFixture } from "@/test/fixtures";

import { AppShell, initialSidebarCollapsed } from "./app-shell";

const project = projectFixture();
const routerPush = vi.hoisted(() => vi.fn());
const developer = {
  display_name: "开发用户",
  email: "dev@example.com",
  id: "user-1",
  must_change_password: false,
  role: "developer" as const,
  status: "active" as const,
};

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects/project-1/datasets",
  useRouter: () => ({ push: routerPush }),
}));

describe("AppShell", () => {
  beforeEach(() => {
    localStorage.clear();
    routerPush.mockClear();
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1280,
      writable: true,
    });
  });

  it("uses desktop collapse only for desktop and mobile navigation below 760px", () => {
    expect(initialSidebarCollapsed(390, "false")).toBe(false);
    expect(initialSidebarCollapsed(1280, "false")).toBe(false);
    expect(initialSidebarCollapsed(1280, "true")).toBe(true);
  });

  it("groups the complete project navigation and keeps system management permission gated", () => {
    render(
      <AppShell
        currentProjectId={project.id}
        onProjectSelect={vi.fn()}
        projects={[project]}
        user={developer}
      >
        <div>Content</div>
      </AppShell>,
    );

    expect(screen.getByText("工作台")).toBeInTheDocument();
    expect(screen.getByText("测试资产")).toBeInTheDocument();
    expect(screen.getByText("执行中心")).toBeInTheDocument();
    expect(screen.getByText("评测与治理")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "测试 Agent" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-agent",
    );
    expect(screen.getByRole("link", { name: "测试用例" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.queryByText("用户与权限")).not.toBeInTheDocument();
  });

  it("uses the typed chromatic-signal icon system across navigation", () => {
    render(
      <AppShell
        currentProjectId={project.id}
        onProjectSelect={vi.fn()}
        projects={[project]}
        user={developer}
      >
        Content
      </AppShell>,
    );

    const navigation = screen.getByRole("navigation", { name: "项目导航" });
    const links = within(navigation).getAllByRole("link");
    const supportedTones = new Set([
      "amber",
      "blue",
      "coral",
      "indigo",
      "mint",
    ]);

    for (const link of links) {
      expect(supportedTones).toContain(
        link.getAttribute("data-navigation-tone"),
      );
      expect(
        link.querySelector('[data-navigation-icon="chromatic-signal"]'),
      ).toBeInTheDocument();
    }

    const datasetLink = screen.getByRole("link", { name: "测试用例" });
    expect(datasetLink).toHaveAttribute("data-navigation-tone", "indigo");
    const icon = datasetLink.querySelector(
      '[data-navigation-icon="chromatic-signal"]',
    );
    expect(icon?.querySelector("svg")).toBeInTheDocument();
    expect(icon?.querySelector("[data-navigation-signal]")).toBeInTheDocument();
  });

  it("keeps a compact pure-navigation sidebar with shared collapsed tooltips", () => {
    render(
      <AppShell
        currentProjectId={project.id}
        onProjectSelect={vi.fn()}
        projects={[project]}
        user={developer}
      >
        Content
      </AppShell>,
    );

    const navigation = screen.getByRole("navigation", { name: "项目导航" });
    expect(navigation).not.toHaveTextContent(/通过率|运行数量|统计/);
    expect(
      navigation.querySelector("[data-navigation-icon-carrier]"),
    ).toHaveClass("app-nav-icon");

    fireEvent.click(screen.getByRole("button", { name: "收起侧边栏" }));

    const collapsedLink = screen.getByRole("link", { name: "测试用例" });
    expect(collapsedLink).not.toHaveAttribute("title");
    expect(
      screen
        .getAllByRole("tooltip")
        .some((tooltip) => tooltip.getAttribute("data-tooltip") === "测试用例"),
    ).toBe(true);
  });

  it("opens the global command palette with Cmd/Ctrl+K and filters routes", () => {
    render(
      <AppShell
        currentProjectId={project.id}
        onProjectSelect={vi.fn()}
        projects={[project]}
        user={developer}
      >
        Content
      </AppShell>,
    );

    fireEvent.keyDown(window, { key: "k", metaKey: true });
    const search = screen.getByRole("searchbox", { name: "全局搜索" });
    expect(search).toHaveFocus();
    fireEvent.change(search, { target: { value: "安全" } });
    const dialog = screen.getByRole("dialog", { name: "全局搜索" });
    expect(
      within(dialog).getByRole("option", { name: "安全测试" }),
    ).toBeInTheDocument();
    expect(
      within(dialog).queryByRole("option", { name: "评分器" }),
    ).not.toBeInTheDocument();

    fireEvent.keyDown(search, { key: "Enter" });
    expect(routerPush).toHaveBeenCalledWith("/projects/project-1/security");
    expect(screen.queryByRole("dialog", { name: "全局搜索" })).toBeNull();
  });

  it("offers quick creation and preserves super administrator access", () => {
    render(
      <AppShell
        currentProjectId={project.id}
        onProjectSelect={vi.fn()}
        projects={[project]}
        user={{ ...developer, role: "super_admin" }}
      >
        Content
      </AppShell>,
    );

    expect(
      screen.getByRole("button", { name: "快速创建" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("运行正常")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "查看运行中心" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs",
    );
    expect(screen.getByRole("link", { name: "用户与权限" })).toHaveAttribute(
      "href",
      "/system/users",
    );
  });

  it("opens a navigation drawer instead of forcing the desktop sidebar on mobile", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 390,
    });
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        addEventListener: vi.fn(),
        matches: query.includes("max-width"),
        media: query,
        removeEventListener: vi.fn(),
      })),
    });

    render(
      <AppShell
        currentProjectId={project.id}
        onProjectSelect={vi.fn()}
        projects={[project]}
        user={developer}
      >
        Content
      </AppShell>,
    );

    fireEvent.click(screen.getByRole("button", { name: "打开导航" }));
    expect(
      screen.getByRole("dialog", { name: "项目导航" }),
    ).toBeInTheDocument();
  });
});
