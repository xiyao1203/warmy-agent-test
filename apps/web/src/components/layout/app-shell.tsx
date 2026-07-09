"use client";

import type {
  ProjectResponse,
  UserResponse,
} from "@warmy/generated-api-client";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  type FocusEvent,
  type MouseEvent,
  type ReactNode,
  useCallback,
  useState,
} from "react";

import { logout } from "@/features/auth";
import { ProjectSwitcher } from "@/features/projects";
import { canManageUsers } from "@/lib/permissions";
import { projectOverviewPath, projectWorkspacePath } from "@/lib/routes";

import { BrandMark } from "./brand-mark";
import { HelpDropdown } from "./help-dropdown";
import { NotificationDropdown } from "./notification-dropdown";
import {
  SidebarColorIcon,
  type SidebarIconName,
  type SidebarIconTone,
} from "./sidebar-icons";
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

type CollapsedSidebarTooltip = {
  label: string;
  top: number;
} | null;

type CollapsedSidebarTooltipController = {
  hide: () => void;
  show: (label: string, target: HTMLElement) => void;
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
  const [collapsedTooltip, setCollapsedTooltip] =
    useState<CollapsedSidebarTooltip>(null);

  const showCollapsedTooltip = useCallback(
    (label: string, target: HTMLElement) => {
      if (!collapsed) return;
      const rect = target.getBoundingClientRect();
      setCollapsedTooltip({ label, top: rect.top + rect.height / 2 });
    },
    [collapsed],
  );

  const hideCollapsedTooltip = useCallback(() => {
    setCollapsedTooltip(null);
  }, []);

  const toggleSidebar = useCallback(() => {
    setCollapsedTooltip(null);
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("sidebar-collapsed", String(next));
      return next;
    });
  }, []);
  const collapsedTooltipController = {
    hide: hideCollapsedTooltip,
    show: showCollapsedTooltip,
  };

  const sidebarWidth = collapsed ? "3.5rem" : "14rem";

  return (
    <div className="h-screen bg-[var(--canvas)] text-[var(--ink)]">
      <header className="flex h-14 items-center justify-between gap-4 border-b border-[var(--hairline)] bg-[var(--canvas)] px-4">
        <div className="flex min-w-0 items-center gap-5">
          <Link
            aria-label="Warmy Agent Test"
            className="font-display flex shrink-0 items-center gap-2 text-base font-semibold"
            href="/login"
          >
            <BrandMark compact={collapsed} />
            {!collapsed && <span>Warmy Agent Test</span>}
          </Link>
          <ProjectSwitcher
            currentProjectId={currentProjectId}
            onSelect={onProjectSelect}
            projects={projects}
          />
        </div>
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
            <ProjectNavLink
              activeMode="exact"
              collapsed={collapsed}
              href="/projects"
              icon={<SidebarNavIcon iconName="project-list" tone="indigo" />}
              label="项目列表"
              tooltip={collapsedTooltipController}
            />
            {activeProjectId ? (
              <>
                <ProjectNavLink
                  collapsed={collapsed}
                  href={projectWorkspacePath(activeProjectId)}
                  icon={<SidebarNavIcon iconName="test-agent" tone="azure" />}
                  label="测试 Agent"
                  tooltip={collapsedTooltipController}
                />
                <OverviewNavLink
                  collapsed={collapsed}
                  href={overviewHref}
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/agents`}
                  icon={<SidebarNavIcon iconName="agent" tone="violet" />}
                  label="智能体"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/datasets`}
                  icon={<SidebarNavIcon iconName="test-case" tone="indigo" />}
                  label="测试用例"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/test-plans`}
                  icon={<SidebarNavIcon iconName="test-plan" tone="amber" />}
                  label="测试计划"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/runs`}
                  icon={<SidebarNavIcon iconName="test-run" tone="emerald" />}
                  label="测试执行"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/environments`}
                  icon={<SidebarNavIcon iconName="environment" tone="teal" />}
                  label="环境与凭证"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/browser-profiles`}
                  icon={
                    <SidebarNavIcon iconName="browser-profile" tone="cyan" />
                  }
                  label="浏览器实例"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/models`}
                  icon={<SidebarNavIcon iconName="model" tone="purple" />}
                  label="模型配置"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/scorers`}
                  icon={<SidebarNavIcon iconName="scorer" tone="orange" />}
                  label="评分器"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/experiments`}
                  icon={<SidebarNavIcon iconName="experiment" tone="fuchsia" />}
                  label="实验对比"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/reviews`}
                  icon={<SidebarNavIcon iconName="review" tone="rose" />}
                  label="人工审核"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/security`}
                  icon={<SidebarNavIcon iconName="security" tone="red" />}
                  label="安全测试"
                  tooltip={collapsedTooltipController}
                />
                <ProjectNavLink
                  collapsed={collapsed}
                  href={`/projects/${activeProjectId}/gates`}
                  icon={<SidebarNavIcon iconName="release-gate" tone="green" />}
                  label="发布门禁"
                  tooltip={collapsedTooltipController}
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
                onBlur={hideCollapsedTooltip}
                onFocus={(event) =>
                  showCollapsedTooltip("用户管理", event.currentTarget)
                }
                onMouseEnter={(event) =>
                  showCollapsedTooltip("用户管理", event.currentTarget)
                }
                onMouseLeave={hideCollapsedTooltip}
                title="用户管理"
              >
                <SidebarNavIcon iconName="user-management" tone="slate-blue" />
                {!collapsed && <span>用户管理</span>}
              </Link>
            </div>
          ) : null}
          <div className="mt-auto border-t border-[var(--hairline)] pt-2">
            <button
              aria-expanded={!collapsed}
              aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
              className={`group relative flex h-9 w-full items-center gap-3 rounded-[var(--radius-sm)] text-sm text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)] ${
                collapsed ? "justify-center px-0" : "px-3"
              }`}
              onBlur={hideCollapsedTooltip}
              onFocus={(event) =>
                showCollapsedTooltip(
                  collapsed ? "展开侧边栏" : "收起侧边栏",
                  event.currentTarget,
                )
              }
              onMouseEnter={(event) =>
                showCollapsedTooltip(
                  collapsed ? "展开侧边栏" : "收起侧边栏",
                  event.currentTarget,
                )
              }
              onMouseLeave={hideCollapsedTooltip}
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
          {collapsedTooltip ? (
            <div
              className="pointer-events-none fixed left-16 z-[80] -translate-y-1/2 whitespace-nowrap rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-2 py-1 text-xs font-medium text-[var(--ink)] shadow-md"
              role="tooltip"
              style={{ top: collapsedTooltip.top }}
            >
              {collapsedTooltip.label}
            </div>
          ) : null}
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
  tooltip,
}: {
  collapsed: boolean;
  href: string;
  tooltip: CollapsedSidebarTooltipController;
}) {
  const pathname = usePathname();
  const isActive = pathname === href;
  const label = "概览";

  function handleTooltipOpen(
    event: FocusEvent<HTMLAnchorElement> | MouseEvent<HTMLAnchorElement>,
  ) {
    tooltip.show(label, event.currentTarget);
  }

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
      onBlur={tooltip.hide}
      onFocus={handleTooltipOpen}
      onMouseEnter={handleTooltipOpen}
      onMouseLeave={tooltip.hide}
      title={label}
    >
      <SidebarNavIcon iconName="overview" tone="sky" />
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}

function SidebarNavIcon({
  iconName,
  tone,
}: {
  iconName: SidebarIconName;
  tone: SidebarIconTone;
}) {
  return <SidebarColorIcon name={iconName} tone={tone} />;
}

function ProjectNavLink({
  collapsed,
  href,
  icon,
  label,
  tooltip,
  activeMode = "section",
}: {
  activeMode?: "exact" | "section";
  collapsed: boolean;
  href: string;
  icon: ReactNode;
  label: string;
  tooltip: CollapsedSidebarTooltipController;
}) {
  const pathname = usePathname();
  const isActive =
    activeMode === "exact"
      ? pathname === href
      : pathname === href || Boolean(pathname?.startsWith(href + "/"));
  function handleTooltipOpen(
    event: FocusEvent<HTMLAnchorElement> | MouseEvent<HTMLAnchorElement>,
  ) {
    tooltip.show(label, event.currentTarget);
  }

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
      onBlur={tooltip.hide}
      onFocus={handleTooltipOpen}
      onMouseEnter={handleTooltipOpen}
      onMouseLeave={tooltip.hide}
      title={label}
    >
      {icon}
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}
