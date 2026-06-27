"use client";

import type {
  ProjectResponse,
  UserResponse,
} from "@warmy/generated-api-client";
import {
  Bell,
  Bot,
  ChevronDown,
  ClipboardCheck,
  Database,
  FlaskConical,
  HelpCircle,
  KeyRound,
  LayoutDashboard,
  MessageSquareText,
  PlayCircle,
  Scale,
  Search,
  Shield,
  ShieldCheck,
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
      <header className="grid h-14 grid-cols-[minmax(16rem,1fr)_minmax(18rem,32rem)_minmax(16rem,1fr)] items-center gap-4 border-b border-[var(--border)] bg-[var(--surface)] px-4 max-[900px]:grid-cols-[1fr_auto]">
        <div className="flex min-w-0 items-center gap-5">
          <Link
            className="shrink-0 text-base font-semibold tracking-tight"
            href={projectHref}
          >
            Warmy Agent Test
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
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <input
            className="h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] pl-9 pr-3 text-sm outline-none placeholder:text-[var(--text-subtle)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
            placeholder="搜索（⌘K）"
            type="search"
          />
        </label>
        <div className="flex items-center justify-end gap-2">
          <button
            aria-label="帮助"
            className="grid size-8 place-items-center rounded-[var(--radius-sm)] text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]"
            type="button"
          >
            <HelpCircle aria-hidden="true" className="size-4" />
          </button>
          <button
            aria-label="通知"
            className="grid size-8 place-items-center rounded-[var(--radius-sm)] text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]"
            type="button"
          >
            <Bell aria-hidden="true" className="size-4" />
          </button>
          <button
            aria-label={`当前用户：${user.display_name}`}
            className="flex h-8 shrink-0 items-center gap-2 rounded-[var(--radius-sm)] px-2 text-sm hover:bg-[var(--surface-subtle)]"
            title={`${user.display_name} · ${user.email}`}
            type="button"
          >
            <span className="grid size-7 place-items-center rounded-full bg-[var(--accent)] text-xs font-semibold text-white">
              {user.display_name.slice(0, 1).toUpperCase()}
            </span>
            <span className="max-[900px]:hidden">{user.display_name}</span>
            <ChevronDown
              aria-hidden="true"
              className="size-3 text-[var(--text-muted)] max-[900px]:hidden"
            />
          </button>
        </div>
      </header>
      <div
        className={
          workspaceMode === "agent"
            ? "grid min-h-[calc(100vh-3.5rem)] grid-cols-[14rem_minmax(0,1fr)_20rem] max-[1279px]:grid-cols-[4rem_minmax(0,1fr)]"
            : "grid min-h-[calc(100vh-3.5rem)] grid-cols-[14rem_minmax(0,1fr)] max-[1279px]:grid-cols-[4rem_minmax(0,1fr)]"
        }
      >
        <aside className="flex flex-col border-r border-[var(--border)] bg-[var(--surface)] p-2">
          <p className="px-3 pb-2 pt-2 text-xs font-medium text-[var(--text-subtle)] max-[1279px]:sr-only">
            项目导航
          </p>
          <nav aria-label="项目导航" className="space-y-1">
            <Link
              className="flex h-9 items-center gap-3 rounded-[var(--radius-sm)] px-3 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)] max-[1279px]:justify-center max-[1279px]:px-0"
              href={projectHref}
              title="概览"
            >
              <LayoutDashboard aria-hidden="true" className="size-4 shrink-0" />
              <span className="max-[1279px]:sr-only">概览</span>
            </Link>
            {activeProjectId ? (
              <>
                <ProjectNavLink
                  href={`/projects/${activeProjectId}/agents`}
                  icon={<Bot aria-hidden="true" className="size-4 shrink-0" />}
                  label="智能体"
                />
                <ProjectNavLink
                  href={`/projects/${activeProjectId}/datasets`}
                  icon={
                    <Database
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="测试用例"
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
                  label="测试执行"
                />
                <ProjectNavLink
                  href={`/projects/${activeProjectId}/environments`}
                  icon={
                    <KeyRound
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="环境与凭证"
                />
                <ProjectNavLink
                  href={`/projects/${activeProjectId}/scorers`}
                  icon={
                    <Scale
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="评分器"
                />
                <ProjectNavLink
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
                  href={`/projects/${activeProjectId}/security`}
                  icon={
                    <Shield
                      aria-hidden="true"
                      className="size-4 shrink-0"
                    />
                  }
                  label="安全测试"
                />
                <ProjectNavLink
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
