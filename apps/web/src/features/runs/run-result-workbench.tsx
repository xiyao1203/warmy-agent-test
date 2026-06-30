"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";

import { TraceTree, type TraceSpan } from "./trace-tree";

type CaseItem = {
  id: string;
  name: string;
  status: "passed" | "failed" | "error" | "running" | "pending";
  duration_ms?: number | null;
  score?: number | null;
  error_type?: string | null;
  error_message?: string | null;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  trace?: TraceSpan[];
};

type RunResultWorkbenchProps = {
  cases: CaseItem[];
  onCaseSelect: (caseId: string) => void;
  projectId: string;
  runId: string;
};

export function RunResultWorkbench({
  cases,
  onCaseSelect,
}: RunResultWorkbenchProps) {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "passed" | "failed" | "error">(
    "all",
  );

  const selectedCase = cases.find((c) => c.id === selectedCaseId);

  const filteredCases = cases.filter((c) => {
    if (filter === "all") return true;
    return c.status === filter;
  });

  const handleCaseClick = (caseId: string) => {
    setSelectedCaseId(caseId);
    onCaseSelect(caseId);
  };

  return (
    <div className="grid h-[calc(100vh-12rem)] grid-cols-[280px_1fr_300px] gap-4">
      {/* 左栏：用例列表 */}
      <div className="flex flex-col overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] p-3">
          <h3 className="text-sm font-semibold">用例列表</h3>
          <div className="mt-2 flex gap-1">
            {(["all", "passed", "failed", "error"] as const).map((f) => (
              <button
                key={f}
                className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
                  filter === f
                    ? "bg-[var(--accent)] text-[var(--accent-foreground)]"
                    : "text-[var(--text-muted)] hover:bg-[var(--surface-subtle)]"
                }`}
                onClick={() => setFilter(f)}
                type="button"
              >
                {f === "all"
                  ? "全部"
                  : f === "passed"
                    ? "通过"
                    : f === "failed"
                      ? "失败"
                      : "错误"}
              </button>
            ))}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {filteredCases.length === 0 ? (
            <p className="p-4 text-center text-sm text-[var(--text-muted)]">
              暂无用例数据
            </p>
          ) : (
            <div className="space-y-1">
              {filteredCases.map((item) => (
                <button
                  key={item.id}
                  className={`flex w-full items-center justify-between rounded px-3 py-2 text-left text-sm transition-colors ${
                    selectedCaseId === item.id
                      ? "bg-[var(--accent-subtle)]"
                      : "hover:bg-[var(--surface-subtle)]"
                  }`}
                  onClick={() => handleCaseClick(item.id)}
                  type="button"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{item.name}</p>
                    <p className="text-xs text-[var(--text-muted)]">
                      {item.duration_ms != null
                        ? `${item.duration_ms}ms`
                        : "未记录"}
                    </p>
                  </div>
                  <Badge
                    tone={
                      item.status === "passed"
                        ? "success"
                        : item.status === "failed"
                          ? "warning"
                          : item.status === "error"
                            ? "danger"
                            : "neutral"
                    }
                  >
                    {item.status === "passed"
                      ? "通过"
                      : item.status === "failed"
                        ? "失败"
                        : item.status === "error"
                          ? "错误"
                          : item.status}
                  </Badge>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 中栏：用例详情 */}
      <div className="flex flex-col overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] p-3">
          <h3 className="text-sm font-semibold">用例详情</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {!selectedCase ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-[var(--text-muted)]">
                请选择一个用例查看详情
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <h4 className="text-lg font-semibold">{selectedCase.name}</h4>
                <div className="mt-2 flex items-center gap-2">
                  <Badge
                    tone={
                      selectedCase.status === "passed"
                        ? "success"
                        : selectedCase.status === "failed"
                          ? "warning"
                          : selectedCase.status === "error"
                            ? "danger"
                            : "neutral"
                    }
                  >
                    {selectedCase.status === "passed"
                      ? "通过"
                      : selectedCase.status === "failed"
                        ? "失败"
                        : selectedCase.status === "error"
                          ? "错误"
                          : selectedCase.status}
                  </Badge>
                  {selectedCase.duration_ms != null && (
                    <span className="text-sm text-[var(--text-muted)]">
                      {selectedCase.duration_ms}ms
                    </span>
                  )}
                </div>
              </div>

              {selectedCase.error_type && (
                <div className="rounded-[var(--radius-sm)] bg-[var(--danger-subtle)] p-3">
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
                  <pre className="mt-2 overflow-auto rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] p-3 text-xs">
                    {JSON.stringify(selectedCase.input, null, 2)}
                  </pre>
                </div>
              )}

              {selectedCase.output && (
                <div>
                  <h5 className="text-sm font-medium">输出</h5>
                  <pre className="mt-2 overflow-auto rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] p-3 text-xs">
                    {JSON.stringify(selectedCase.output, null, 2)}
                  </pre>
                </div>
              )}

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
      <div className="flex flex-col overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] p-3">
          <h3 className="text-sm font-semibold">评分结果</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {!selectedCase ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-[var(--text-muted)]">
                请选择一个用例查看评分
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {selectedCase.score != null ? (
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4 text-center">
                  <p className="text-sm text-[var(--text-muted)]">综合评分</p>
                  <p className="mt-2 text-4xl font-bold">
                    {selectedCase.score.toFixed(2)}
                  </p>
                  <p className="mt-2 text-sm text-[var(--text-muted)]">
                    {selectedCase.score >= 0.8
                      ? "优秀"
                      : selectedCase.score >= 0.6
                        ? "良好"
                        : "需要改进"}
                  </p>
                </div>
              ) : (
                <div className="rounded-[var(--radius-md)] border border-dashed border-[var(--border)] p-4 text-center">
                  <p className="text-sm text-[var(--text-muted)]">
                    暂无评分数据
                  </p>
                </div>
              )}

              <div className="space-y-2">
                <h5 className="text-sm font-medium">状态统计</h5>
                <div className="grid grid-cols-2 gap-2">
                  <div className="rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] p-2 text-center">
                    <p className="text-xs text-[var(--text-muted)]">通过</p>
                    <p className="text-lg font-semibold text-[var(--success)]">
                      {cases.filter((c) => c.status === "passed").length}
                    </p>
                  </div>
                  <div className="rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] p-2 text-center">
                    <p className="text-xs text-[var(--text-muted)]">失败</p>
                    <p className="text-lg font-semibold text-[var(--warning)]">
                      {cases.filter((c) => c.status === "failed").length}
                    </p>
                  </div>
                  <div className="rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] p-2 text-center">
                    <p className="text-xs text-[var(--text-muted)]">错误</p>
                    <p className="text-lg font-semibold text-[var(--danger)]">
                      {cases.filter((c) => c.status === "error").length}
                    </p>
                  </div>
                  <div className="rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] p-2 text-center">
                    <p className="text-xs text-[var(--text-muted)]">总计</p>
                    <p className="text-lg font-semibold">{cases.length}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
