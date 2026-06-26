"use client";

import type { RunCaseResponse, RunResponse } from "@warmy/generated-api-client";
import { AlertTriangle, ListTree, Square } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { StatusBadge } from "./run-center";

export function RunDetail({
  cases = [],
  loading = false,
  onCancel = async () => undefined,
  run,
}: {
  cases?: RunCaseResponse[];
  loading?: boolean;
  onCancel?: () => Promise<unknown>;
  run?: RunResponse;
}) {
  if (loading || !run) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        正在加载运行详情…
      </div>
    );
  }
  const canCancel = run.status === "queued" || run.status === "running";
  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Run {run.id.slice(0, 8)}
          </h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {run.passed_cases} 通过 · {run.failed_cases} 失败 ·{" "}
            {run.error_cases} 错误 · {run.cancelled_cases} 已取消
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={run.status} />
          <Button disabled={!canCancel} onClick={onCancel}>
            <Square aria-hidden="true" className="mr-1.5 size-4" />
            取消运行
          </Button>
        </div>
      </header>
      <section className="mt-5 grid gap-4">
        {cases.map((item) => (
          <article
            className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4"
            key={item.id}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-medium">{item.name}</h2>
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  {item.duration_ms == null ? "未记录耗时" : `${item.duration_ms} ms`}
                </p>
              </div>
              <StatusBadge status={item.status} />
            </div>
            {item.error_type ? (
              <div className="mt-4 rounded-[var(--radius-sm)] bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]">
                <div className="flex items-center gap-2 font-medium">
                  <AlertTriangle aria-hidden="true" className="size-4" />
                  {item.error_type}
                </div>
                <p className="mt-1">{item.error_message}</p>
              </div>
            ) : null}
            {item.output ? (
              <pre className="mt-4 overflow-auto rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] p-3 text-xs">
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
                      className="rounded-[var(--radius-sm)] border border-[var(--border)] p-3 text-xs"
                      key={index}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">
                          {String(span.name ?? `span-${index + 1}`)}
                        </span>
                        <Badge>{String(span.status ?? "recorded")}</Badge>
                      </div>
                      <pre className="mt-2 overflow-auto text-[var(--text-muted)]">
                        {JSON.stringify(span, null, 2)}
                      </pre>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[var(--text-muted)]">暂无 Trace</p>
                )}
              </div>
            </details>
          </article>
        ))}
      </section>
    </div>
  );
}
