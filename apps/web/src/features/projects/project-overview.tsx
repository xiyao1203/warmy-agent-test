import type {
  ProjectMemberResponse,
  ProjectResponse,
  UserResponse,
} from "@warmy/generated-api-client";
import { Archive, Folder, Users } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton, SkeletonText } from "@/components/uiverse";
import { Tooltip } from "@/components/uiverse";

type ProjectOverviewProps = {
  assetSummary?: {
    agents: number;
    datasets: number;
    testPlans: number;
  };
  error?: "not-found" | "service";
  loading?: boolean;
  members?: ProjectMemberResponse[];
  project?: ProjectResponse;
  user: UserResponse;
};

const memberRoleLabels = {
  developer: "开发",
  reviewer: "审核",
  tester: "测试",
  viewer: "只读",
} as const;

export function ProjectOverview({
  assetSummary = { agents: 0, datasets: 0, testPlans: 0 },
  error,
  loading = false,
  members = [],
  project,
  user,
}: ProjectOverviewProps) {
  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error === "not-found") {
    return (
      <StatusPanel
        description="请确认项目地址，或联系超级管理员检查项目成员关系。"
        title="项目不存在或你无权访问"
      />
    );
  }

  if (error === "service" || !project) {
    return (
      <StatusPanel
        description="服务暂时没有响应，请稍后刷新页面重试。"
        title="项目概览暂时不可用"
      />
    );
  }

  const currentMembership = members.find(
    (member) => member.user_id === user.id,
  );
  const accessLabel =
    user.role === "super_admin"
      ? "超级管理员"
      : currentMembership
        ? memberRoleLabels[currentMembership.role]
        : "项目成员";

  return (
    <div className="mx-auto max-w-[1180px] px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">
              {project.name}
            </h1>
            {project.archived ? <Badge tone="warning">已归档</Badge> : null}
          </div>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            项目 ID：{project.id}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-[var(--text-muted)]">我的权限</p>
          <p className="mt-1 text-sm font-medium">{accessLabel}</p>
        </div>
      </header>

      <section className="grid grid-cols-3 border-b border-[var(--border)] py-5 max-[900px]:grid-cols-1 max-[900px]:gap-4">
        <Metric
          icon={<Folder className="size-4" />}
          label="项目状态"
          tooltip="项目当前状态：活跃或已归档"
        >
          {project.archived ? "已归档" : "活跃"}
        </Metric>
        <Metric
          icon={<Users className="size-4" />}
          label="项目成员"
          tooltip="项目成员数量和列表"
        >
          {members.length} 位成员
        </Metric>
        <Metric
          icon={<Archive className="size-4" />}
          label="测试资产"
          tooltip="项目中的 Agents、数据集和测试计划数量"
        >
          <span className="flex flex-wrap gap-x-3 gap-y-1">
            <span>{assetSummary.agents} Agents</span>
            <span>{assetSummary.datasets} 数据集</span>
            <span>{assetSummary.testPlans} 测试计划</span>
          </span>
        </Metric>
      </section>

      <div className="grid grid-cols-[minmax(0,1.6fr)_minmax(18rem,0.7fr)] gap-6 py-6 max-[1000px]:grid-cols-1">
        <section className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
          <div className="border-b border-[var(--border)] px-4 py-3">
            <h2 className="text-sm font-semibold">项目成员</h2>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              当前 API 仅提供成员标识和项目角色。
            </p>
          </div>
          {members.length ? (
            <Table>
              <TableHeader className="bg-[var(--surface-subtle)]">
                <TableRow>
                  <TableHead>成员标识</TableHead>
                  <TableHead>项目角色</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow
                    className="transition-colors hover:bg-[var(--surface-subtle)]"
                    key={member.user_id}
                  >
                    <TableCell className="font-mono text-xs">
                      {member.user_id}
                      {member.user_id === user.id ? (
                        <span className="ml-2 text-[var(--text-muted)]">
                          （你）
                        </span>
                      ) : null}
                    </TableCell>
                    <TableCell>
                      <Badge tone="neutral">
                        {memberRoleLabels[member.role]}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              description="此项目还没有普通成员，超级管理员仍可访问项目。"
              title="暂无项目成员"
            />
          )}
        </section>

        <section className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
          <div className="border-b border-[var(--border)] px-4 py-3">
            <h2 className="text-sm font-semibold">测试活动</h2>
          </div>
          <EmptyState
            description="运行记录、进度与结果可在运行中心查看。"
            title="查看运行中心"
          />
        </section>
      </div>
    </div>
  );
}

function Metric({
  children,
  icon,
  label,
  tooltip,
}: {
  children: ReactNode;
  icon: ReactNode;
  label: string;
  tooltip?: string;
}) {
  return (
    <div className="flex items-start gap-3 border-r border-[var(--border)] px-5 first:pl-0 last:border-r-0 max-[900px]:border-r-0 max-[900px]:px-0">
      <Tooltip content={tooltip || label}>
        <span className="mt-0.5 text-[var(--text-muted)]">{icon}</span>
      </Tooltip>
      <div>
        <p className="text-xs text-[var(--text-muted)]">{label}</p>
        <p className="mt-1 text-sm font-medium">{children}</p>
      </div>
    </div>
  );
}

function StatusPanel({
  description,
  title,
}: {
  description?: string;
  title: string;
}) {
  return (
    <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
      <div>
        <h1 className="text-base font-semibold">{title}</h1>
        {description ? (
          <p className="mt-2 max-w-md text-sm leading-6 text-[var(--text-muted)]">
            {description}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="mx-auto max-w-[1180px] px-6 py-6">
      {/* Header skeleton */}
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="mt-2 h-4 w-32" />
        </div>
        <div className="text-right">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="mt-1 h-4 w-12" />
        </div>
      </div>

      {/* Metrics skeleton */}
      <div className="grid grid-cols-3 border-b border-[var(--border)] py-5 max-[900px]:grid-cols-1 max-[900px]:gap-4">
        <div className="flex items-start gap-3 border-r border-[var(--border)] px-5 first:pl-0 last:border-r-0 max-[900px]:border-r-0 max-[900px]:px-0">
          <Skeleton className="size-4" />
          <div>
            <Skeleton className="h-3 w-12" />
            <Skeleton className="mt-1 h-4 w-16" />
          </div>
        </div>
        <div className="flex items-start gap-3 border-r border-[var(--border)] px-5 max-[900px]:border-r-0 max-[900px]:px-0">
          <Skeleton className="size-4" />
          <div>
            <Skeleton className="h-3 w-12" />
            <Skeleton className="mt-1 h-4 w-20" />
          </div>
        </div>
        <div className="flex items-start gap-3 px-5 max-[900px]:px-0">
          <Skeleton className="size-4" />
          <div>
            <Skeleton className="h-3 w-12" />
            <Skeleton className="mt-1 h-4 w-40" />
          </div>
        </div>
      </div>

      {/* Content skeleton */}
      <div className="grid grid-cols-[minmax(0,1.6fr)_minmax(18rem,0.7fr)] gap-6 py-6 max-[1000px]:grid-cols-1">
        <div className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
          <div className="border-b border-[var(--border)] px-4 py-3">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="mt-1 h-3 w-48" />
          </div>
          <div className="p-4">
            <SkeletonText lines={3} />
          </div>
        </div>
        <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
          <div className="border-b border-[var(--border)] px-4 py-3">
            <Skeleton className="h-4 w-20" />
          </div>
          <div className="p-4">
            <SkeletonText lines={2} />
          </div>
        </div>
      </div>
    </div>
  );
}
