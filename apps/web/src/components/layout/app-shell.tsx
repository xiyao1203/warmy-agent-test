"use client";

import type {
  ProjectResponse,
  UserResponse,
} from "@warmy/generated-api-client";
import {
  Bot,
  ClipboardCheck,
  Database,
  LayoutDashboard,
  PlayCircle,
  Users,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { ProjectSwitcher } from "@/features/projects";
import { canManageUsers } from "@/lib/permissions";

type AppShellProps = {
  children: ReactNode;
  currentProjectId?: string;
  onProjectSelect: (projectId: string) => void;
  projects: ProjectResponse[];
  user: UserResponse;
  workspaceMode?: "agent" | "management";
};

export function AppShell({
  children,
  currentProjectId,
  onProjectSelect,
  projects,
  user,
  workspaceMode = "management",
}: AppShellProps) {
  const projectHref = currentProjectId
    ? `/projects/${currentProjectId}/overview`
    : "/projects";

  const activeProjectId = currentProjectId || (projects.length > 0 ? projects[0].id : null);

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--text)]">
      <header className="flex h-12 items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-4">
        <div className="flex min-w-0 items-center gap-5">
          <Link className="shrink-0 text-sm font-semibold" href={projectHref}>
            Warmy Agent Test
          </Link>
          <ProjectSwitcher
            currentProjectId={currentProjectId}
            onSelect={onProjectSelect}
            projects={projects}
          />
        </div>
        <button
          aria-label={`当前用户：${user.display_name}`}
          className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[var(--surface-subtle)] text-xs font-semibold"
          title={`${user.display_name} · ${user.email}`}
          type="button"
        >
          {user.display_name.slice(0, 1).toUpperCase()}
        </button>
      </header>
      <div
        className={
          workspaceMode === "agent"
            ? "grid min-h-[calc(100vh-3rem)] grid-cols-[14rem_minmax(0,1fr)_20rem] max-[1279px]:grid-cols-[4rem_minmax(0,1fr)]"
            : "grid min-h-[calc(100vh-3rem)] grid-cols-[14rem_minmax(0,1fr)] max-[1279px]:grid-cols-[4rem_minmax(0,1fr)]"
        }
      >
        <aside className="flex flex-col border-r border-[var(--border)] bg-[var(--surface)] p-2">
          <nav aria-label="项目导航" className="space-y-1">
            <Link
              className="flex h-9 items-center gap-3 rounded-[var(--radius-sm)] px-3 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)] max-[1279px]:justify-center max-[1279px]:px-0"
              href={projectHref}
              title="项目概览"
            >
              <LayoutDashboard aria-hidden="true" className="size-4 shrink-0" />
              <span className="max-[1279px]:sr-only">项目概览</span>
            </Link>
            {activeProjectId ? (
              <>
                <ProjectNavLink
                  href={`/projects/${activeProjectId}/agents`}
                  icon={<Bot aria-hidden="true" className="size-4 shrink-0" />}
                  label="Agent 与版本"
                />
                <ProjectNavLink
                  href={`/projects/${activeProjectId}/datasets`}
                  icon={
                    <Database
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="数据集与用例"
                />
                <ProjectNavLink
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
                  href={`/projects/${activeProjectId}/runs`}
                  icon={
                    <PlayCircle
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="运行中心"
                />
              </>
            ) : null}
          </nav>
          {canManageUsers(user) ? (
            <div className="mt-auto border-t border-[var(--border)] pt-3">
              <p className="px-3 pb-1.5 text-xs font-medium text-[var(--text-subtle)] max-[1279px]:sr-only">
                系统管理
              </p>
              <Link
                className="flex h-9 items-center gap-3 rounded-[var(--radius-sm)] px-3 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)] max-[1279px]:justify-center max-[1279px]:px-0"
                href="/system/users"
                title="用户管理"
              >
                <Users aria-hidden="true" className="size-4 shrink-0" />
                <span className="max-[1279px]:sr-only">用户管理</span>
              </Link>
            </div>
          ) : null}
        </aside>
        <main className="min-w-0">{children}</main>
        {workspaceMode === "agent" ? (
          <aside className="border-l border-[var(--border)] bg-[var(--surface)] max-[1279px]:hidden" />
        ) : null}
      </div>
    </div>
  );
}

function ProjectNavLink({
  href,
  icon,
  label,
}: {
  href: string;
  icon: ReactNode;
  label: string;
}) {
  return (
    <Link
      className="flex h-9 items-center gap-3 rounded-[var(--radius-sm)] px-3 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)] max-[1279px]:justify-center max-[1279px]:px-0"
      href={href}
      title={label}
    >
      {icon}
      <span className="max-[1279px]:sr-only">{label}</span>
    </Link>
  );
}
