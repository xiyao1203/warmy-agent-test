"use client";

import type {
  ProjectResponse,
  UserResponse,
} from "@warmy/generated-api-client";
import {
  Bot,
  ClipboardCheck,
  Database,
  FlaskConical,
  Globe,
  KeyRound,
  LayoutDashboard,
  MessageSquareText,
  Cpu,
  PanelLeftClose,
  PanelLeftOpen,
  PlayCircle,
  Scale,
  Search,
  Shield,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useCallback, useState } from "react";

import { logout } from "@/features/auth";
import { ProjectSwitcher } from "@/features/projects";
import { canManageUsers } from "@/lib/permissions";
import { projectOverviewPath, projectWorkspacePath } from "@/lib/routes";

import { HelpDropdown } from "./help-dropdown";
import { NotificationDropdown } from "./notification-dropdown";
import { ThemeToggle } from "./theme-toggle";
import { UserDropdown } from "./user-dropdown";

type AppShellProps = {
  children: ReactNode;
  currentProjectId?: string;
  onProjectSelect: (projectId: string) => void;
  projects: ProjectResponse[];
  user: UserResponse;
  workspaceMode?: "agent" | "management";
};

export function initialSidebarCollapsed(
  viewportWidth: number,
  storedPreference: string | null,
) {
  return viewportWidth < 760 || storedPreference === "true";
}

export function AppShell({
  children,
  currentProjectId,
  onProjectSelect,
  projects,
  user,
  workspaceMode = "management",
}: AppShellProps) {
  const activeProjectId =
    currentProjectId || (projects.length > 0 ? projects[0].id : null);
  const projectHref = activeProjectId
    ? projectWorkspacePath(activeProjectId)
    : "/projects";
  const overviewHref = activeProjectId
    ? projectOverviewPath(activeProjectId)
    : "/projects";

  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return initialSidebarCollapsed(
      window.innerWidth,
      localStorage.getItem("sidebar-collapsed"),
    );
  });

  const toggleSidebar = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("sidebar-collapsed", String(next));
      return next;
    });
  }, []);

  const sidebarWidth = collapsed ? "3.5rem" : "14rem";

  return (
    <div className="h-screen bg-[var(--canvas)] text-[var(--ink)]">
      <header className="grid h-14 grid-cols-[minmax(16rem,1fr)_minmax(18rem,32rem)_minmax(16rem,1fr)] items-center gap-4 border-b border-[var(--hairline)] bg-[var(--canvas)] px-4 max-[900px]:grid-cols-[1fr_auto]">
        <div className="flex min-w-0 items-center gap-5">
          <Link
            className="shrink-0 text-base font-semibold tracking-tight"
            href={projectHref}
          >
            {collapsed ? "AT" : "Agent Test"}
          </Link>
          <ProjectSwitcher
            currentProjectId={currentProjectId}
            onSelect={onProjectSelect}
            projects={projects}
          />
        </div>
        <label className="relative max-[900px]:hidden">
          <span className="sr-only">全局搜索</span>
          <Search
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]"
          />
          <input
            className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] pl-9 pr-3 text-sm outline-none placeholder:text-[var(--body)] focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
            placeholder="搜索（⌘K）"
            type="search"
          />
        </label>
        <div className="flex items-center justify-end gap-1">
          <ThemeToggle />
          <HelpDropdown />
          <NotificationDropdown />
          <UserDropdown
            displayName={user.display_name}
            email={user.email}
            onLogout={async () => {
              await logout();
              window.location.assign("/login");
            }}
          />
        </div>
      </header>
      <div className="flex h-[calc(100vh-3.5rem)]">
        <aside
          className="flex shrink-0 flex-col border-r border-[var(--hairline)] bg-[var(--surface)] p-2 transition-[width] duration-200"
          style={{ width: sidebarWidth }}
        >
          {!collapsed && (
            <p className="px-3 pb-2 pt-2 text-[11px] font-semibold uppercase tracking-[0.66px] text-[var(--body)]">
              项目导航
            </p>
          )}
          <nav
            aria-label="项目导航"
            className="flex-1 space-y-1 overflow-y-auto min-h-0"
          >
            {activeProjectId ? (
              <>
                <ProjectNavLink
                  collapsed={collapsed}
                  href={projectWorkspacePath(activeProjectId)}
                  icon={
                    <Sparkles aria-hidden="true" className="size-4 shrink-0" />
                  }
                  label="测试 Agent"
                />
                <OverviewNavLink collapsed={collapsed} href={overviewHref} />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/agents`}
                  icon={<Bot aria-hidden="true" className="size-4 shrink-0" />}
                  label="智能体"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/datasets`}
                  icon={
                    <Database aria-hidden="true" className="size-4 shrink-0" />
                  }
                  label="测试用例"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/test-plans`}
                  icon={
                    <ClipboardCheck
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="测试计划"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/runs`}
                  icon={
                    <PlayCircle
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="测试执行"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/environments`}
                  icon={
                    <KeyRound aria-hidden="true" className="size-4 shrink-0" />
                  }
                  label="环境与凭证"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/browser-profiles`}
                  icon={
                    <Globe aria-hidden="true" className="size-4 shrink-0" />
                  }
                  label="浏览器实例"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/models`}
                  icon={<Cpu aria-hidden="true" className="size-4 shrink-0" />}
                  label="模型配置"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/scorers`}
                  icon={
                    <Scale aria-hidden="true" className="size-4 shrink-0" />
                  }
                  label="评分器"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/experiments`}
                  icon={
                    <FlaskConical
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="实验对比"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/reviews`}
                  icon={
                    <MessageSquareText
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="人工审核"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/security`}
                  icon={
                    <Shield aria-hidden="true" className="size-4 shrink-0" />
                  }
                  label="安全测试"
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/gates`}
                  icon={
                    <ShieldCheck
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="发布门禁"
                />
              </>
            ) : null}
          </nav>
          {canManageUsers(user) ? (
            <div className="border-t border-[var(--hairline)] pt-3">
              {!collapsed && (
                <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-[0.66px] text-[var(--body)]">
                  系统管理
                </p>
              )}
              <Link
                className={`flex h-9 items-center gap-3 rounded-[var(--radius-sm)] text-sm text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)] ${
                  collapsed ? "justify-center px-0" : "px-3"
                }`}
                href="/system/users"
                title="用户管理"
              >
                <Users aria-hidden="true" className="size-4 shrink-0" />
                {!collapsed && <span>用户管理</span>}
              </Link>
            </div>
          ) : null}
          <div className="mt-auto border-t border-[var(--hairline)] pt-2">
            <button
              aria-expanded={!collapsed}
              aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
              className={`flex h-9 w-full items-center gap-3 rounded-[var(--radius-sm)] text-sm text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)] ${
                collapsed ? "justify-center px-0" : "px-3"
              }`}
              onClick={toggleSidebar}
              title={collapsed ? "展开侧边栏" : "收起侧边栏"}
              type="button"
            >
              {collapsed ? (
                <PanelLeftOpen aria-hidden="true" className="size-4 shrink-0" />
              ) : (
                <PanelLeftClose
                  aria-hidden="true"
                  className="size-4 shrink-0"
                />
              )}
              {!collapsed && <span>收起菜单</span>}
            </button>
          </div>
        </aside>
        <main className="min-w-0 flex-1 overflow-y-auto">{children}</main>
        {workspaceMode === "agent" ? (
          <aside className="border-l border-[var(--hairline)] bg-[var(--surface)] max-[1279px]:hidden" />
        ) : null}
      </div>
    </div>
  );
}

function OverviewNavLink({
  collapsed,
  href,
}: {
  collapsed: boolean;
  href: string;
}) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      className={`flex h-9 items-center gap-3 rounded-[var(--radius-sm)] text-sm transition-colors ${
        collapsed ? "justify-center px-0" : "px-3"
      } ${
        isActive
          ? "bg-[var(--primary-subtle)] font-medium text-[var(--primary)]"
          : "text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
      }`}
      href={href}
      title="概览"
    >
      <LayoutDashboard aria-hidden="true" className="size-4 shrink-0" />
      {!collapsed && <span>概览</span>}
    </Link>
  );
}

function ProjectNavLink({
  collapsed,
  href,
  icon,
  label,
}: {
  collapsed: boolean;
  href: string;
  icon: ReactNode;
  label: string;
}) {
  const pathname = usePathname();
  const isActive =
    pathname === href || Boolean(pathname?.startsWith(href + "/"));

  return (
    <Link
      className={`flex h-9 items-center gap-3 rounded-[var(--radius-sm)] text-sm transition-colors ${
        collapsed ? "justify-center px-0" : "px-3"
      } ${
        isActive
          ? "bg-[var(--primary-subtle)] font-medium text-[var(--primary)]"
          : "text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
      }`}
      href={href}
      title={label}
    >
      {icon}
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}
