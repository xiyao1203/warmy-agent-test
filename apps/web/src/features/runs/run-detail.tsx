"use client";

import type { RunCaseResponse, RunResponse } from "@warmy/generated-api-client";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  ListTree,
  Radio,
  Square,
  Upload,
} from "lucide-react";
import { useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton, SkeletonText } from "@/components/uiverse";
import { Tooltip } from "@/components/uiverse";

import type { ArtifactItem } from "./api";
import { artifactDownloadUrl, uploadArtifact } from "./api";
import { ReportDownloadButton } from "./report-download-button";
import { StatusBadge } from "./run-center";
import { TraceTimeline, TraceTree, type TraceSpan } from "./trace-tree";

export function RunDetail({
  artifacts = [],
  cases = [],
  loading = false,
  onCancel = async () => undefined,
  projectId,
  run,
  traceSpans = [],
}: {
  artifacts?: ArtifactItem[];
  cases?: RunCaseResponse[];
  loading?: boolean;
  onCancel?: () => Promise<unknown>;
  projectId: string;
  run?: RunResponse;
  traceSpans?: TraceSpan[];
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [cancelling, setCancelling] = useState(false);
  const [activeTab, setActiveTab] = useState<
    "overview" | "cases" | "trace" | "artifacts"
  >("overview");
  if (loading || !run) {
    return <RunDetailSkeleton />;
  }
  const canCancel = run.status === "queued" || run.status === "running";
  const finishedCases =
    run.passed_cases + run.failed_cases + run.error_cases + run.cancelled_cases;
  const progress = run.total_cases
    ? Math.round((finishedCases / run.total_cases) * 100)
    : 0;
  return (
    <div className="min-w-0 bg-[var(--canvas)] px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <p className="text-xs font-medium text-[var(--body)]">
            运行详情
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">
            Run {run.id.slice(0, 8)}
          </h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {run.passed_cases} 通过 · {run.failed_cases} 失败 ·{" "}
            {run.error_cases} 错误 · {run.cancelled_cases} 已取消
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={run.status} />
          <Tooltip content="下载测试报告（JSON/JUnit/HTML）">
            <ReportDownloadButton projectId={projectId} runId={run.id} />
          </Tooltip>
          <Tooltip
            content={
              canCancel
                ? "取消正在运行的测试"
                : "只有排队中或运行中的任务才能取消"
            }
          >
            <Button
              disabled={!canCancel || cancelling}
              loading={cancelling}
              onClick={async () => {
                setCancelling(true);
                try {
                  await onCancel();
                } finally {
                  setCancelling(false);
                }
              }}
            >
              <Square aria-hidden="true" className="mr-1.5 size-4" />
              取消运行
            </Button>
          </Tooltip>
        </div>
      </header>
      {/* Tabs */}
      <nav className="mt-5 flex gap-1 border-b border-[var(--hairline)]">
        {(
          [
            ["overview", "概览"],
            ["cases", "用例列表"],
            ["trace", "Trace"],
            ["artifacts", "产物"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            className={`rounded-t px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === key
                ? "border-b-2 border-[var(--primary)] text-[var(--primary)]"
                : "text-[var(--muted)] hover:text-[var(--ink)]"
            }`}
            onClick={() => setActiveTab(key)}
            type="button"
          >
            {label}
          </button>
        ))}
      </nav>

      {/* Overview Tab */}
      {activeTab === "overview" ? (
        <div className="mt-5 grid grid-cols-[minmax(0,1fr)_22rem] gap-5 max-[1100px]:grid-cols-1">
          <section className="space-y-3">
            <div className="rounded border border-[var(--hairline)] bg-[var(--surface)] p-5">
              <h3 className="text-sm font-semibold">执行摘要</h3>
              <dl className="mt-3 grid grid-cols-4 gap-3">
                <SummaryItem label="总用例" value={String(run.total_cases)} />
                <SummaryItem label="通过" value={String(run.passed_cases)} />
                <SummaryItem label="失败" value={String(run.failed_cases)} />
                <SummaryItem label="错误" value={String(run.error_cases)} />
              </dl>
            </div>
          </section>
          <aside className="h-fit rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-base font-semibold">执行摘要</h2>
              <Badge tone={canCancel ? "accent" : "neutral"}>
                <Radio aria-hidden="true" className="mr-1 size-3" />
                {canCancel ? "实时刷新" : "已结束"}
              </Badge>
            </div>
            <div className="mt-5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[var(--muted)]">完成进度</span>
                <span className="font-medium">{progress}%</span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--canvas-soft)]">
                <div
                  className="h-full rounded-full bg-[var(--primary)]"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
            <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
              <SummaryItem label="总用例" value={String(run.total_cases)} />
              <SummaryItem label="已完成" value={String(finishedCases)} />
              <SummaryItem label="通过" value={String(run.passed_cases)} />
              <SummaryItem
                label="失败/错误"
                value={String(run.failed_cases + run.error_cases)}
              />
            </dl>
            <div className="mt-5 space-y-3 border-t border-[var(--hairline)] pt-5 text-sm">
              <InfoRow label="Workflow" value={run.workflow_id ?? "待启动"} />
              <InfoRow
                label="创建时间"
                value={new Date(run.created_at).toLocaleString("zh-CN")}
              />
              <InfoRow
                label="开始时间"
                value={
                  run.started_at
                    ? new Date(run.started_at).toLocaleString("zh-CN")
                    : "未开始"
                }
              />
              <InfoRow
                label="完成时间"
                value={
                  run.completed_at
                    ? new Date(run.completed_at).toLocaleString("zh-CN")
                    : "进行中"
                }
              />
            </div>
            <div className="mt-5 rounded-[var(--radius-md)] bg-[var(--canvas-soft)] p-3 text-xs leading-5 text-[var(--muted)]">
              <div className="flex items-center gap-2 font-medium text-[var(--ink)]">
                <CheckCircle2 aria-hidden="true" className="size-4" />
                Trace 会随运行结果持续更新
              </div>
              <p className="mt-1">
                SSE 可用时实时刷新；断线后自动回退到查询刷新。
              </p>
            </div>
          </aside>
        </div>
      ) : null}

      {/* Cases Tab */}
      {activeTab === "cases" ? (
        <section className="mt-5 grid gap-4">
          {cases.length === 0 ? (
            <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-8 text-center">
              <p className="text-sm font-medium text-[var(--muted)]">
                暂无用例数据
              </p>
            </div>
          ) : (
            cases.map((item) => (
              <article
                className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-4"
                key={item.id}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="font-medium">{item.name}</h2>
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      {item.duration_ms == null
                        ? "未记录耗时"
                        : `${item.duration_ms} ms`}
                    </p>
                  </div>
                  <StatusBadge status={item.status} />
                </div>
                {item.error_type ? (
                  <div className="mt-4 rounded-[var(--radius-md)] bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]">
                    <div className="flex items-center gap-2 font-medium">
                      <AlertTriangle aria-hidden="true" className="size-4" />
                      {item.error_type}
                    </div>
                    <p className="mt-1">{item.error_message}</p>
                  </div>
                ) : null}
                {item.output ? (
                  <pre className="mt-4 overflow-auto rounded-[var(--radius-md)] bg-[var(--canvas-soft)] p-3 text-xs">
                    {JSON.stringify(item.output, null, 2)}
                  </pre>
                ) : null}
                <details className="mt-4" open={item.status === "error"}>
                  <summary className="flex cursor-pointer items-center gap-2 text-sm font-medium">
                    <ListTree aria-hidden="true" className="size-4" />
                    Trace
                  </summary>
                  <div className="mt-3 space-y-2">
                    {item.trace.length ? (
                      item.trace.map((span, index) => (
                        <div
                          className="rounded-[var(--radius-md)] border border-[var(--hairline)] p-3 text-xs"
                          key={index}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-medium">
                              {String(span.name ?? `span-${index + 1}`)}
                            </span>
                            <Badge>{String(span.status ?? "recorded")}</Badge>
                          </div>
                          <pre className="mt-2 overflow-auto text-[var(--muted)]">
                            {JSON.stringify(span, null, 2)}
                          </pre>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-[var(--muted)]">
                        暂无 Trace
                      </p>
                    )}
                  </div>
                </details>
              </article>
            ))
          )}
        </section>
      ) : null}

      {/* Trace Tab */}
      {activeTab === "trace" ? (
        <section className="mt-5 space-y-5">
          <div>
            <h3 className="mb-3 text-sm font-semibold">Trace 树</h3>
            <TraceTree spans={traceSpans} />
          </div>
          {traceSpans.length > 0 ? (
            <div>
              <h3 className="mb-3 text-sm font-semibold">时间线</h3>
              <TraceTimeline spans={traceSpans} />
            </div>
          ) : null}
        </section>
      ) : null}

      {/* Artifacts Tab */}
      {activeTab === "artifacts" ? (
        <section className="mt-6 pt-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <FileText aria-hidden="true" className="size-4" />
              运行产物
            </h2>
            <div className="flex items-center gap-2">
              <input
                accept="*/*"
                className="hidden"
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (!file) return;
                  setUploading(true);
                  setUploadError("");
                  try {
                    await uploadArtifact(projectId, run.id, file);
                    window.location.reload();
                  } catch {
                    setUploadError("上传失败，请重试。");
                  } finally {
                    setUploading(false);
                    event.target.value = "";
                  }
                }}
                ref={fileInputRef}
                type="file"
              />
              <Button
                disabled={uploading}
                loading={uploading}
                onClick={() => fileInputRef.current?.click()}
                variant="ghost"
              >
                <Upload aria-hidden="true" className="size-4" />
              </Button>
            </div>
          </div>
          {uploadError && (
            <p className="mt-2 text-sm text-[var(--danger)]">{uploadError}</p>
          )}
          {artifacts.length === 0 ? (
            <p className="mt-3 text-sm text-[var(--muted)]">
              暂无产物，点击上传按钮添加。
            </p>
          ) : (
            <ul className="mt-3 divide-y divide-[var(--hairline)] rounded-[var(--radius-md)] border border-[var(--hairline)]">
              {artifacts.map((a) => (
                <li
                  key={a.id}
                  className="flex items-center justify-between gap-3 px-3 py-2.5"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{a.filename}</p>
                    <p className="text-xs text-[var(--muted)]">
                      {a.content_type} · {formatBytes(a.size_bytes)} ·{" "}
                      {new Date(a.created_at).toLocaleDateString("zh-CN")}
                    </p>
                  </div>
                  <Button asChild className="shrink-0" variant="ghost">
                    <a
                      download={a.filename}
                      href={artifactDownloadUrl(projectId, a.id)}
                    >
                      <Download aria-hidden="true" className="size-4" />
                    </a>
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--hairline)] p-3">
      <dt className="text-xs text-[var(--muted)]">{label}</dt>
      <dd className="mt-1 text-lg font-semibold">{value}</dd>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="text-[var(--muted)]">{label}</span>
      <span className="max-w-44 break-all text-right font-medium">{value}</span>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function RunDetailSkeleton() {
  return (
    <div className="min-w-0 bg-[var(--canvas)] px-6 py-6">
      {/* Header skeleton */}
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <Skeleton className="h-3 w-16" />
          <Skeleton className="mt-1 h-8 w-32" />
          <Skeleton className="mt-2 h-4 w-48" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-6 w-20" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-20" />
        </div>
      </header>

      {/* Summary skeleton */}
      <dl className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="rounded-[var(--radius-md)] border border-[var(--hairline)] p-3"
          >
            <Skeleton className="h-3 w-12" />
            <Skeleton className="mt-1 h-7 w-16" />
          </div>
        ))}
      </dl>

      {/* Tabs skeleton */}
      <div className="mt-6 border-b border-[var(--hairline)]">
        <div className="flex gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-16" />
          ))}
        </div>
      </div>

      {/* Content skeleton */}
      <div className="mt-6">
        <SkeletonText lines={5} />
      </div>
    </div>
  );
}
