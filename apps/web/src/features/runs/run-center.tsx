"use client";

import type { RunResponse } from "@warmy/generated-api-client";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Database,
  Play,
  RotateCcw,
  Search,
  Square,
  Timer,
  Eye,
} from "lucide-react";
import Link from "next/link";
import { type ReactNode, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { ResourceReferenceLink } from "@/components/ui/resource-reference-link";
import { problemMessage } from "@/lib/api/problem";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TableActionButton } from "@/components/ui/table-actions";
import { TruncatedText } from "@/components/ui/truncated-text";

type PlanVersionOption = { id: string; label: string };
type CreatedRun = { id?: string } | void;

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
  onCreate?: (testPlanVersionId: string) => Promise<CreatedRun>;
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
      `${run.id} ${run.run_number} ${run.workflow_id ?? ""} ${run.status}`.toLowerCase();
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
      setActionError(runErrorMessage(error));
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
            选择已发布测试计划版本启动真实执行，并查看进度、结果与 Trace。
          </p>
        </div>
        <div className="flex items-end gap-2">
          <label className="text-sm font-medium">
            测试计划版本
            <DropdownSelect
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
            </DropdownSelect>
          </label>
          <Button
            disabled={!versionId || busy}
            onClick={submit}
            variant="primary"
          >
            <Play aria-hidden="true" className="mr-1.5 size-4" />
            启动测试执行
          </Button>
        </div>
      </header>
      <section className="mt-5 grid gap-3 md:grid-cols-4">
        <FlowCard
          description="Agent、用例、环境和评分器"
          href={`/projects/${projectId}/test-plans`}
          icon={<ClipboardCheck aria-hidden="true" className="size-4" />}
          label="1. 发布测试计划"
        />
        <FlowCard
          description="选择版本后启动真实执行"
          icon={<Play aria-hidden="true" className="size-4" />}
          label="2. 启动运行"
        />
        <FlowCard
          description="详情页实时刷新"
          icon={<Timer aria-hidden="true" className="size-4" />}
          label="3. 查看进度"
        />
        <FlowCard
          description="Trace、产物和失败证据"
          icon={<Database aria-hidden="true" className="size-4" />}
          label="4. 分析结果"
        />
      </section>
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
            <DropdownSelect
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
            </DropdownSelect>
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
            description={
              runs.length
                ? "换个关键词或状态筛选再试试。"
                : planVersions.length
                  ? "选择上方已发布测试计划版本，点击“启动测试执行”。"
                  : "先去测试计划里配置并发布一个版本，发布后才能启动运行。"
            }
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
              ) : planVersions.length ? undefined : (
                <Button asChild variant="secondary">
                  <Link href={`/projects/${projectId}/test-plans`}>
                    去配置测试计划
                  </Link>
                </Button>
              )
            }
            title={runs.length ? "没有匹配的运行" : "暂无运行记录"}
          />
        ) : (
          <Table className="w-full table-fixed">
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead className="w-[18%]">运行</TableHead>
                <TableHead className="w-[28%]">执行资产</TableHead>
                <TableHead className="w-[10%]">状态</TableHead>
                <TableHead className="w-[16%]">进度与结果</TableHead>
                <TableHead className="w-[20%]">资源消耗</TableHead>
                <TableHead className="w-20">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRuns.map((run) => (
                <TableRow
                  className="hover:bg-[var(--canvas-soft)]"
                  key={run.id}
                >
                  <TableCell>
                    <div className="mx-auto flex w-fit min-w-0 items-center gap-3 text-left">
                      <span className="grid size-8 place-items-center rounded-[var(--radius-md)] bg-[var(--canvas-soft)]">
                        <Activity aria-hidden="true" className="size-4" />
                      </span>
                      <div>
                        <TruncatedText
                          className="font-medium"
                          value={run.run_number}
                        >
                          {run.run_number}
                        </TruncatedText>
                        <TruncatedText className="mt-0.5 text-xs text-[var(--muted)]">
                          Workflow {run.workflow_id ?? "待启动"}
                        </TruncatedText>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="space-y-1 text-left text-xs">
                    <p>
                      计划：
                      <ResourceReferenceLink reference={run.plan_ref} />
                    </p>
                    <p>
                      Agent：
                      <ResourceReferenceLink reference={run.agent_ref} />
                    </p>
                    <p>
                      用例集：
                      <ResourceReferenceLink reference={run.dataset_ref} />
                    </p>
                    {run.source_case_ref ? (
                      <p>
                        来源用例：
                        <ResourceReferenceLink
                          reference={run.source_case_ref}
                        />
                      </p>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={run.status} />
                  </TableCell>
                  <TableCell className="text-left text-xs leading-5 text-[var(--muted)]">
                    <p>
                      {Math.round((run.progress ?? 0) * 100)}% ·{" "}
                      {run.passed_cases +
                        run.failed_cases +
                        run.error_cases +
                        run.cancelled_cases}{" "}
                      / {run.total_cases}
                    </p>
                    <p>
                      通过 {run.passed_cases} · 失败 {run.failed_cases} · 错误{" "}
                      {run.error_cases}
                    </p>
                    <p>触发方式 {run.trigger_type || "manual"}</p>
                  </TableCell>
                  <TableCell className="text-left text-xs leading-5 text-[var(--muted)]">
                    <p>
                      耗时{" "}
                      {run.duration_ms == null
                        ? "暂无数据"
                        : `${run.duration_ms} ms`}{" "}
                      · Token {run.token_usage?.total ?? "暂无数据"}
                    </p>
                    <p>
                      成本 {run.cost == null ? "暂无数据" : run.cost.toFixed(4)}
                    </p>
                    <p>
                      <ResourceReferenceLink
                        emptyLabel="创建者暂无数据"
                        reference={run.created_by_ref}
                      />
                    </p>
                    <p>{new Date(run.created_at).toLocaleString("zh-CN")}</p>
                  </TableCell>
                  <TableCell>
                    <TableActionButton
                      asChild
                      label={`查看运行 ${run.id} 结果`}
                    >
                      <Link href={`/projects/${projectId}/runs/${run.id}`}>
                        <Eye aria-hidden="true" />
                      </Link>
                    </TableActionButton>
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

function FlowCard({
  description,
  href,
  icon,
  label,
}: {
  description: string;
  href?: string;
  icon: ReactNode;
  label: string;
}) {
  const content = (
    <>
      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)]">
        {icon}
      </span>
      <span className="min-w-0">
        <span className="block font-medium">{label}</span>
        <span className="block truncate text-xs text-[var(--muted)]">
          {description}
        </span>
      </span>
    </>
  );

  if (href) {
    return (
      <Link
        className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm transition-colors hover:border-[var(--primary)]"
        href={href}
      >
        {content}
      </Link>
    );
  }

  return (
    <div className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm">
      {content}
    </div>
  );
}

function runErrorMessage(error: unknown) {
  const raw = problemMessage(error, "启动运行失败，请稍后重试。");
  if (raw.includes("Run execution runtime is unavailable")) {
    return "运行服务暂不可用：请确认 Temporal 和 API Runner 已启动后重试。";
  }
  if (raw.includes("Published test plan has no test cases")) {
    return "这个测试计划没有可运行用例：请先在测试用例中添加并发布用例集。";
  }
  if (raw.includes("Idempotency-Key is required")) {
    return "启动请求缺少幂等标识，请刷新页面后重试。";
  }
  return raw;
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
