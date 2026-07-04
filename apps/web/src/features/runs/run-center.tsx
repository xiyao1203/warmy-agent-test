"use client";

import type { RunResponse } from "@warmy/generated-api-client";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Play,
  RotateCcw,
  Search,
  Square,
  Timer,
} from "lucide-react";
import Link from "next/link";
import { type ReactNode, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { problemMessage } from "@/lib/api/problem";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type PlanVersionOption = { id: string; label: string };

export function RunCenter({
  error,
  loading = false,
  onCreate = async () => undefined,
  planVersions = [],
  projectId,
  runs = [],
}: {
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (testPlanVersionId: string) => Promise<unknown>;
  planVersions?: PlanVersionOption[];
  projectId: string;
  runs?: RunResponse[];
}) {
  const [versionId, setVersionId] = useState(planVersions[0]?.id ?? "");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const summary = useMemo(() => summarizeRuns(runs), [runs]);
  const filteredRuns = runs.filter((run) => {
    const matchesStatus = statusFilter === "all" || run.status === statusFilter;
    const haystack =
      `${run.id} ${run.workflow_id ?? ""} ${run.status}`.toLowerCase();
    return matchesStatus && haystack.includes(query.trim().toLowerCase());
  });
  if (loading) return <StatusPanel title="正在加载运行中心…" />;
  if (error === "not-found")
    return <StatusPanel title="项目不存在或你无权访问" />;
  if (error === "service") return <StatusPanel title="运行中心暂时不可用" />;
  async function submit() {
    if (!versionId) return;
    setBusy(true);
    setActionError("");
    try {
      await onCreate(versionId);
    } catch (error) {
      setActionError(problemMessage(error, "启动运行失败，请稍后重试。"));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="min-w-0 bg-[var(--canvas)] px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium text-[var(--body)]">测试执行</p>
          <h1 className="text-2xl font-semibold tracking-tight">运行中心</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            基于已发布测试计划启动 API Agent 执行，并查看进度、结果与 Trace。
          </p>
        </div>
        <div className="flex items-end gap-2">
          <label className="text-sm font-medium">
            测试计划版本
            <select
              className="mt-1.5 h-9 min-w-56 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-2 text-sm"
              onChange={(event) => setVersionId(event.target.value)}
              value={versionId}
            >
              <option value="">请选择已发布版本</option>
              {planVersions.map((version) => (
                <option key={version.id} value={version.id}>
                  {version.label}
                </option>
              ))}
            </select>
          </label>
          <Button
            disabled={!versionId || busy}
            onClick={submit}
            variant="primary"
          >
            <Play aria-hidden="true" className="mr-1.5 size-4" />
            开始运行
          </Button>
        </div>
      </header>
      {actionError ? (
        <p className="mt-3 text-sm text-[var(--danger)]" role="alert">
          {actionError}
        </p>
      ) : null}
      <section className="mt-5 grid grid-cols-4 gap-3 max-[1100px]:grid-cols-2 max-[700px]:grid-cols-1">
        <SummaryCard
          icon={<Activity aria-hidden="true" className="size-4" />}
          label="总运行"
          value={String(summary.total)}
        />
        <SummaryCard
          icon={<Timer aria-hidden="true" className="size-4" />}
          label="运行中"
          value={String(summary.active)}
        />
        <SummaryCard
          icon={<CheckCircle2 aria-hidden="true" className="size-4" />}
          label="通过率"
          value={`${summary.passRate}%`}
        />
        <SummaryCard
          icon={<AlertTriangle aria-hidden="true" className="size-4" />}
          label="异常运行"
          value={String(summary.unhealthy)}
        />
      </section>
      <section className="mt-5 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--hairline)] px-4 py-3">
          <label className="relative min-w-[18rem] flex-1 text-sm">
            <span className="sr-only">搜索运行</span>
            <Search
              aria-hidden="true"
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]"
            />
            <Input
              aria-label="搜索运行"
              className="pl-9"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索 Run ID、Workflow 或状态"
              value={query}
            />
          </label>
          <label className="text-sm">
            <span className="sr-only">运行状态</span>
            <select
              aria-label="运行状态"
              className="h-9 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-2 text-sm"
              onChange={(event) => setStatusFilter(event.target.value)}
              value={statusFilter}
            >
              <option value="all">状态：全部</option>
              <option value="queued">排队中</option>
              <option value="running">运行中</option>
              <option value="passed">已通过</option>
              <option value="failed">断言失败</option>
              <option value="error">执行错误</option>
              <option value="cancelled">已取消</option>
            </select>
          </label>
          <Button
            disabled={!query && statusFilter === "all"}
            onClick={() => {
              setQuery("");
              setStatusFilter("all");
            }}
          >
            重置
          </Button>
        </div>
        {!filteredRuns.length ? (
          <EmptyState
            action={
              runs.length ? (
                <Button
                  onClick={() => {
                    setQuery("");
                    setStatusFilter("all");
                  }}
                  variant="secondary"
                >
                  清除筛选
                </Button>
              ) : undefined
            }
            description={
              runs.length
                ? "换个关键词或状态筛选再试试。"
                : "选择一个已发布测试计划版本后启动首个运行。"
            }
            title={runs.length ? "没有匹配的运行" : "暂无运行记录"}
          />
        ) : (
          <Table>
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead>运行</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>进度</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="w-24 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRuns.map((run) => (
                <TableRow
                  className="hover:bg-[var(--canvas-soft)]"
                  key={run.id}
                >
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <span className="grid size-8 place-items-center rounded-[var(--radius-md)] bg-[var(--canvas-soft)]">
                        <Activity aria-hidden="true" className="size-4" />
                      </span>
                      <div>
                        <p className="font-medium">Run {run.id.slice(0, 8)}</p>
                        <p className="mt-0.5 text-xs text-[var(--muted)]">
                          Workflow {run.workflow_id ?? "待启动"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={run.status} />
                  </TableCell>
                  <TableCell className="text-sm">
                    {run.passed_cases +
                      run.failed_cases +
                      run.error_cases +
                      run.cancelled_cases}{" "}
                    / {run.total_cases}
                  </TableCell>
                  <TableCell className="text-sm text-[var(--muted)]">
                    {new Date(run.created_at).toLocaleString("zh-CN")}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button asChild variant="ghost">
                      <Link href={`/projects/${projectId}/runs/${run.id}`}>
                        查看
                      </Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "passed"
      ? "success"
      : status === "failed" || status === "error"
        ? "danger"
        : status === "cancelled"
          ? "warning"
          : "accent";
  const icon =
    status === "passed" ? (
      <CheckCircle2 aria-hidden="true" className="mr-1 size-3" />
    ) : status === "failed" || status === "error" ? (
      <AlertTriangle aria-hidden="true" className="mr-1 size-3" />
    ) : status === "cancelled" ? (
      <Square aria-hidden="true" className="mr-1 size-3" />
    ) : (
      <RotateCcw aria-hidden="true" className="mr-1 size-3 animate-spin" />
    );
  return (
    <Badge tone={tone}>
      {icon}
      {status}
    </Badge>
  );
}

function StatusPanel({ title }: { title: string }) {
  return (
    <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
      <div>
        <h1 className="text-base font-semibold">{title}</h1>
        <p className="mt-2 max-w-md text-sm leading-6 text-[var(--muted)]">
          请稍后刷新重试，或联系超级管理员。
        </p>
      </div>
    </div>
  );
}

function SummaryCard({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <article className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-[var(--muted)]">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
        </div>
        <span className="grid size-9 place-items-center rounded-full bg-[var(--canvas-soft)] text-[var(--muted)]">
          {icon}
        </span>
      </div>
    </article>
  );
}

function summarizeRuns(runs: RunResponse[]) {
  const total = runs.length;
  const passed = runs.filter((run) => run.status === "passed").length;
  const active = runs.filter((run) =>
    ["queued", "running"].includes(run.status),
  ).length;
  const unhealthy = runs.filter((run) =>
    ["failed", "error", "cancelled"].includes(run.status),
  ).length;
  return {
    active,
    passRate: total ? Math.round((passed / total) * 100) : 0,
    total,
    unhealthy,
  };
}
