"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  FileJson,
  GitBranch,
  Search,
} from "lucide-react";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { TraceTree, type TraceSpan } from "./trace-tree";

type CaseStatus =
  | "cancelled"
  | "error"
  | "failed"
  | "passed"
  | "pending"
  | "queued"
  | "running";

type CaseItem = {
  id: string;
  name: string;
  status: CaseStatus;
  duration_ms?: number | null;
  score?: number | null;
  error_type?: string | null;
  error_message?: string | null;
  input?: Record<string, unknown> | null;
  output?: Record<string, unknown> | null;
  trace?: TraceSpan[];
  evidence?: {
    execution_outcome?: string;
    quality_decision?: string;
    security_decision?: string;
    canvas?: { nodes?: unknown[]; connections?: unknown[] };
    artifacts?: unknown[];
  } | null;
};

type RunResultWorkbenchProps = {
  cases: CaseItem[];
  onCaseSelect: (caseId: string) => void;
  projectId: string;
  runId: string;
};

type StatusFilter = "all" | CaseStatus;

const STATUS_FILTERS: Array<{ label: string; value: StatusFilter }> = [
  { label: "全部", value: "all" },
  { label: "通过", value: "passed" },
  { label: "失败", value: "failed" },
  { label: "错误", value: "error" },
  { label: "运行中", value: "running" },
  { label: "排队中", value: "queued" },
  { label: "已取消", value: "cancelled" },
];

export function RunResultWorkbench({
  cases,
  onCaseSelect,
}: RunResultWorkbenchProps) {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(() =>
    readQueryParam("case"),
  );
  const [filter, setFilter] = useState<StatusFilter>(() =>
    readStatusFilterParam(),
  );
  const [query, setQuery] = useState(() => readQueryParam("q") ?? "");

  const statusCounts = useMemo(() => getStatusCounts(cases), [cases]);
  const normalizedQuery = query.trim().toLowerCase();

  const filteredCases = useMemo(
    () =>
      cases
        .filter((c) => {
          if (filter === "all") return true;
          return c.status === filter;
        })
        .filter((c) => matchesQuery(c, normalizedQuery)),
    [cases, filter, normalizedQuery],
  );

  const activeCaseId =
    selectedCaseId && filteredCases.some((c) => c.id === selectedCaseId)
      ? selectedCaseId
      : (filteredCases[0]?.id ?? null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setOrDeleteParam(params, "status", filter === "all" ? "" : filter);
    setOrDeleteParam(params, "q", query.trim());
    setOrDeleteParam(params, "case", activeCaseId ?? "");
    const nextQuery = params.toString();
    const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}`;
    if (nextUrl !== `${window.location.pathname}${window.location.search}`) {
      window.history.replaceState(null, "", nextUrl);
    }
  }, [activeCaseId, filter, query]);

  const selectedCase = cases.find((c) => c.id === activeCaseId);
  const selectedEvidence = selectedCase
    ? summarizeEvidence(selectedCase)
    : null;

  const handleCaseClick = (caseId: string) => {
    setSelectedCaseId(caseId);
    onCaseSelect(caseId);
  };

  return (
    <div className="grid h-[calc(100vh-12rem)] grid-cols-[minmax(16rem,18rem)_minmax(0,1fr)_minmax(18rem,20rem)] gap-4 max-[1180px]:grid-cols-[minmax(15rem,17rem)_minmax(0,1fr)] max-[880px]:h-auto max-[880px]:grid-cols-1">
      {/* 左栏：用例列表 */}
      <div className="flex flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        <div className="space-y-3 border-b border-[var(--hairline)] p-3">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold">用例列表</h3>
            <span className="text-xs text-[var(--muted)]">
              {filteredCases.length} / {cases.length}
            </span>
          </div>
          <label className="relative block">
            <span className="sr-only">搜索用例</span>
            <Search
              aria-hidden="true"
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]"
            />
            <Input
              aria-label="搜索用例"
              className="h-9 rounded-[var(--radius-md)] pl-9"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索名称、错误或 Trace"
              value={query}
            />
          </label>
          <div className="flex flex-wrap gap-1">
            {STATUS_FILTERS.map((item) => (
              <button
                aria-pressed={filter === item.value}
                key={item.value}
                className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
                  filter === item.value
                    ? "bg-[var(--primary)] text-white"
                    : "text-[var(--muted)] hover:bg-[var(--canvas-soft)]"
                }`}
                onClick={() => setFilter(item.value)}
                type="button"
              >
                {item.label}{" "}
                {countForFilter(item.value, statusCounts, cases.length)}
              </button>
            ))}
          </div>
          {(filter !== "all" || query.trim()) && (
            <Button
              className="h-8 w-full"
              onClick={() => {
                setFilter("all");
                setQuery("");
              }}
              type="button"
              variant="ghost"
            >
              清除筛选
            </Button>
          )}
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {cases.length === 0 ? (
            <p className="p-4 text-center text-sm text-[var(--muted)]">
              暂无用例数据
            </p>
          ) : filteredCases.length === 0 ? (
            <div className="p-4 text-center text-sm text-[var(--muted)]">
              <p className="font-medium text-[var(--ink)]">没有匹配的用例</p>
              <p className="mt-1">换个状态或关键词再试。</p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredCases.map((item) => (
                <button
                  key={item.id}
                  className={`flex w-full items-center justify-between rounded px-3 py-2 text-left text-sm transition-colors ${
                    activeCaseId === item.id
                      ? "bg-[var(--primary-subtle)]"
                      : "hover:bg-[var(--canvas-soft)]"
                  }`}
                  onClick={() => handleCaseClick(item.id)}
                  type="button"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{item.name}</p>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      {item.duration_ms != null
                        ? `${item.duration_ms} ms`
                        : "未记录耗时"}{" "}
                      · {item.trace?.length ?? 0} Trace
                    </p>
                  </div>
                  <Badge tone={statusTone(item.status)}>
                    {statusLabel(item.status)}
                  </Badge>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 中栏：用例详情 */}
      <div className="flex flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        <div className="border-b border-[var(--hairline)] p-3">
          <h3 className="text-sm font-semibold">用例详情</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {!selectedCase ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-[var(--muted)]">
                {filteredCases.length
                  ? "请选择一个用例查看详情"
                  : "当前筛选下暂无可查看用例"}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <h4 className="text-lg font-semibold">{selectedCase.name}</h4>
                <div className="mt-2 flex items-center gap-2">
                  <Badge tone={statusTone(selectedCase.status)}>
                    {statusLabel(selectedCase.status)}
                  </Badge>
                  {selectedCase.duration_ms != null && (
                    <span className="text-sm text-[var(--muted)]">
                      {selectedCase.duration_ms} ms
                    </span>
                  )}
                </div>
              </div>

              {selectedCase.evidence ? (
                <DecisionSummary evidence={selectedCase.evidence} />
              ) : null}

              {selectedCase.status === "failed" ||
              selectedCase.status === "error" ? (
                <FailureExplanation status={selectedCase.status} />
              ) : null}

              {selectedCase.error_type && (
                <div className="rounded-[var(--radius-md)] bg-[var(--danger-subtle)] p-3">
                  <p className="text-sm font-medium text-[var(--danger)]">
                    {selectedCase.error_type}
                  </p>
                  {selectedCase.error_message && (
                    <p className="mt-1 text-sm text-[var(--danger)]">
                      {selectedCase.error_message}
                    </p>
                  )}
                </div>
              )}

              {selectedCase.input && (
                <div>
                  <h5 className="text-sm font-medium">输入</h5>
                  <pre className="mt-2 overflow-auto rounded-[var(--radius-md)] bg-[var(--canvas-soft)] p-3 text-xs">
                    {JSON.stringify(selectedCase.input, null, 2)}
                  </pre>
                </div>
              )}

              {selectedCase.output && (
                <div>
                  <h5 className="text-sm font-medium">输出</h5>
                  <pre className="mt-2 overflow-auto rounded-[var(--radius-md)] bg-[var(--canvas-soft)] p-3 text-xs">
                    {JSON.stringify(selectedCase.output, null, 2)}
                  </pre>
                </div>
              )}

              {selectedEvidence ? (
                <EvidenceSummary evidence={selectedEvidence} />
              ) : null}

              {selectedCase.trace && selectedCase.trace.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium">Trace</h5>
                  <div className="mt-2">
                    <TraceTree spans={selectedCase.trace} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 右栏：评分面板 */}
      <div className="flex flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] max-[1180px]:col-span-2 max-[880px]:col-span-1">
        <div className="border-b border-[var(--hairline)] p-3">
          <h3 className="text-sm font-semibold">评分结果</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {!selectedCase ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-[var(--muted)]">
                请选择一个用例查看评分
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {selectedCase.score != null ? (
                <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-4 text-center">
                  <p className="text-sm text-[var(--muted)]">综合评分</p>
                  <p className="mt-2 text-4xl font-bold">
                    {selectedCase.score.toFixed(2)}
                  </p>
                  <p className="mt-2 text-sm text-[var(--muted)]">
                    {selectedCase.score >= 0.8
                      ? "优秀"
                      : selectedCase.score >= 0.6
                        ? "良好"
                        : "需要改进"}
                  </p>
                </div>
              ) : (
                <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--hairline)] p-4 text-center">
                  <p className="text-sm text-[var(--muted)]">暂无评分数据</p>
                </div>
              )}

              <div className="space-y-2">
                <h5 className="text-sm font-medium">全量状态统计</h5>
                <div className="grid grid-cols-2 gap-2">
                  <StatusStat
                    label="通过"
                    tone="success"
                    value={statusCounts.passed}
                  />
                  <StatusStat
                    label="失败"
                    tone="warning"
                    value={statusCounts.failed}
                  />
                  <StatusStat
                    label="错误"
                    tone="danger"
                    value={statusCounts.error}
                  />
                  <StatusStat label="总计" value={cases.length} />
                </div>
              </div>

              {selectedCase.status === "failed" ||
              selectedCase.status === "error" ? (
                <div className="rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3 text-sm">
                  <div className="flex items-center gap-2 font-medium">
                    <AlertTriangle aria-hidden="true" className="size-4" />
                    定位建议
                  </div>
                  <p className="mt-1 text-[var(--muted)]">
                    {selectedCase.status === "failed"
                      ? "先核对断言、输出和业务状态差异，再回看 Trace 中最后一次工具或模型步骤。"
                      : "先核对环境、凭证、超时、网络和 Worker 日志，再判断是否需要重试。"}
                  </p>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DecisionSummary({
  evidence,
}: {
  evidence: NonNullable<CaseItem["evidence"]>;
}) {
  const execution =
    evidence.execution_outcome === "success" ? "执行成功" : "执行异常";
  const quality =
    evidence.quality_decision === "pass"
      ? "质量通过"
      : evidence.quality_decision === "fail"
        ? "质量未通过"
        : "等待复核";
  const security =
    evidence.security_decision === "clear"
      ? "安全通过"
      : evidence.security_decision === "blocked"
        ? "安全阻断"
        : "存在安全发现";
  return (
    <section
      aria-label="执行质量与安全判定"
      className="rounded-[var(--radius-md)] border border-[var(--hairline)] p-3"
    >
      <div className="flex flex-wrap gap-2">
        <Badge
          tone={evidence.execution_outcome === "success" ? "success" : "danger"}
        >
          {execution}
        </Badge>
        <Badge
          tone={evidence.quality_decision === "pass" ? "success" : "warning"}
        >
          {quality}
        </Badge>
        <Badge
          tone={evidence.security_decision === "clear" ? "success" : "danger"}
        >
          {security}
        </Badge>
      </div>
      <div className="mt-2 flex gap-2 text-xs text-[var(--muted)]">
        <span>{evidence.canvas?.nodes?.length ?? 0} 个节点</span>
        <span>{evidence.artifacts?.length ?? 0} 个产物</span>
      </div>
    </section>
  );
}

function EvidenceSummary({
  evidence,
}: {
  evidence: {
    cost: number;
    durationLabel: string;
    hasOutput: boolean;
    tokenCount: number;
    traceCount: number;
  };
}) {
  return (
    <section
      aria-label="当前用例证据概览"
      className="rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3"
    >
      <div className="flex items-center gap-2 text-sm font-medium">
        <FileJson aria-hidden="true" className="size-4" />
        证据概览
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-5">
        <EvidenceMetric
          icon={<GitBranch aria-hidden="true" className="size-3.5" />}
          label="Trace"
          value={`${evidence.traceCount} 个`}
        />
        <EvidenceMetric
          icon={<CheckCircle2 aria-hidden="true" className="size-3.5" />}
          label="输出"
          value={evidence.hasOutput ? "已记录" : "未记录"}
        />
        <EvidenceMetric
          icon={<Clock3 aria-hidden="true" className="size-3.5" />}
          label="耗时"
          value={evidence.durationLabel}
        />
        <EvidenceMetric label="Token" value={String(evidence.tokenCount)} />
        <EvidenceMetric label="费用" value={`¥${evidence.cost.toFixed(2)}`} />
      </dl>
    </section>
  );
}

function EvidenceMetric({
  icon,
  label,
  value,
}: {
  icon?: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[var(--radius-sm)] bg-[var(--surface)] p-2">
      <dt className="flex items-center gap-1 text-xs text-[var(--muted)]">
        {icon}
        {label}
      </dt>
      <dd className="mt-1 font-semibold">{value}</dd>
    </div>
  );
}

function FailureExplanation({ status }: { status: CaseStatus }) {
  const isError = status === "error";
  return (
    <div
      className={`rounded-[var(--radius-md)] border p-3 ${
        isError
          ? "border-[var(--danger)] bg-[var(--danger-subtle)]"
          : "border-[var(--warning)] bg-[var(--warning-subtle)]"
      }`}
    >
      <div className="flex items-center gap-2 text-sm font-semibold">
        <AlertTriangle aria-hidden="true" className="size-4" />
        {isError ? "执行错误" : "断言未通过"}
      </div>
      <p className="mt-1 text-sm text-[var(--muted)]">
        {isError
          ? "优先排查环境、凭证、超时、网络或 Worker 错误；这类问题不等同于 Agent 能力失败。"
          : "被测 Agent 已完成但结果不符合预期；优先对照输出、业务状态和断言配置。"}
      </p>
    </div>
  );
}

function StatusStat({
  label,
  tone,
  value,
}: {
  label: string;
  tone?: "danger" | "success" | "warning";
  value: number;
}) {
  const toneClass =
    tone === "success"
      ? "text-[var(--success)]"
      : tone === "warning"
        ? "text-[var(--warning)]"
        : tone === "danger"
          ? "text-[var(--danger)]"
          : "";
  return (
    <div className="rounded-[var(--radius-md)] bg-[var(--canvas-soft)] p-2 text-center">
      <p className="text-xs text-[var(--muted)]">{label}</p>
      <p className={`text-lg font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}

function getStatusCounts(cases: CaseItem[]) {
  return cases.reduce(
    (acc, item) => {
      acc[item.status] += 1;
      return acc;
    },
    {
      error: 0,
      failed: 0,
      passed: 0,
      pending: 0,
      queued: 0,
      running: 0,
      cancelled: 0,
    } satisfies Record<CaseStatus, number>,
  );
}

function countForFilter(
  filter: StatusFilter,
  counts: Record<CaseStatus, number>,
  total: number,
) {
  if (filter === "all") return total;
  return counts[filter];
}

function matchesQuery(item: CaseItem, query: string) {
  if (!query) return true;
  const haystack = [
    item.name,
    item.status,
    statusLabel(item.status),
    item.error_type,
    item.error_message,
    safeStringify(item.input),
    safeStringify(item.output),
    ...(item.trace ?? []).flatMap((span) => [
      span.id,
      span.name,
      span.event_type,
      span.status,
      safeStringify(span.payload),
    ]),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
}

function readQueryParam(name: string) {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get(name);
}

function readStatusFilterParam(): StatusFilter {
  const raw = readQueryParam("status");
  if (
    raw === "passed" ||
    raw === "failed" ||
    raw === "error" ||
    raw === "running" ||
    raw === "pending" ||
    raw === "queued" ||
    raw === "cancelled"
  ) {
    return raw;
  }
  return "all";
}

function setOrDeleteParam(
  params: URLSearchParams,
  name: string,
  value: string,
) {
  if (value) {
    params.set(name, value);
  } else {
    params.delete(name);
  }
}

function summarizeEvidence(item: CaseItem) {
  const trace = item.trace ?? [];
  const tokenCount = trace.reduce(
    (sum, span) => sum + (span.token_count ?? 0),
    0,
  );
  const cost = trace.reduce((sum, span) => sum + (span.cost ?? 0), 0);
  return {
    cost,
    durationLabel:
      item.duration_ms == null ? "未记录" : `${item.duration_ms} ms`,
    hasOutput: item.output != null,
    tokenCount,
    traceCount: trace.length,
  };
}

function safeStringify(value: unknown) {
  if (value == null) return "";
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function statusLabel(status: CaseStatus) {
  switch (status) {
    case "passed":
      return "通过";
    case "failed":
      return "失败";
    case "error":
      return "错误";
    case "running":
      return "运行中";
    case "queued":
      return "排队中";
    case "cancelled":
      return "已取消";
    case "pending":
      return "待执行";
  }
}

function statusTone(
  status: CaseStatus,
): "accent" | "danger" | "neutral" | "success" | "warning" {
  switch (status) {
    case "passed":
      return "success";
    case "failed":
      return "warning";
    case "error":
      return "danger";
    case "running":
      return "accent";
    case "queued":
      return "neutral";
    case "cancelled":
      return "neutral";
    case "pending":
      return "neutral";
  }
}
