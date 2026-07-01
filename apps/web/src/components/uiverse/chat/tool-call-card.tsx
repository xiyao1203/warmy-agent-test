"use client";

import React from "react";

import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  Database,
  FlaskConical,
  Loader2,
  PlayCircle,
  RefreshCw,
  Scale,
  Shield,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useState } from "react";

const agentIcons: Record<string, typeof Bot> = {
  target_agent: Bot,
  test_data: Database,
  test_plan: ClipboardCheck,
  execution: PlayCircle,
  evaluation: Scale,
  security: Shield,
  review_gate: ShieldCheck,
  experiment: FlaskConical,
  environment: Shield,
};

const agentLabels: Record<string, string> = {
  target_agent: "被测 Agent",
  test_data: "测试数据",
  test_plan: "测试计划",
  execution: "执行引擎",
  evaluation: "评测",
  security: "安全",
  review_gate: "审核门禁",
  experiment: "实验",
  environment: "环境",
};

export type TaskState = {
  taskId: string;
  childAgent: string;
  capability: string;
  inputSummary: string;
  status: "delegated" | "running" | "completed" | "failed";
  output: Record<string, unknown> | null;
  errorDetail: string | null;
  onRetry?: (taskId: string) => void;
};

export function ToolCallCard({ task }: { task: TaskState }) {
  const [expanded, setExpanded] = useState(false);
  const IconComp = agentIcons[task.childAgent] ?? Bot;
  const label = agentLabels[task.childAgent] ?? task.childAgent;
  const hasDetails =
    task.inputSummary ||
    (task.status === "completed" && task.output) ||
    task.status === "failed";

  const statusConfig = STATUS_MAP[task.status];

  return (
    <div
      className={`group my-1.5 overflow-hidden rounded-[var(--radius-md)] border transition-colors ${
        task.status === "failed"
          ? "border-[var(--danger)]/30 bg-[var(--danger-subtle)]/10"
          : "border-[var(--hairline)] bg-[var(--surface)] hover:border-[var(--primary)]/30"
      }`}
    >
      {/* Header row */}
      <button
        className="flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-[var(--canvas-soft)]/50"
        disabled={!hasDetails}
        onClick={() => hasDetails && setExpanded((v) => !v)}
        type="button"
      >
        <span className="flex size-5 shrink-0 items-center justify-center rounded bg-[var(--canvas-soft)] text-[var(--muted)]">
          <IconComp className="size-3" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="text-[0.7rem] font-medium text-[var(--ink)]">
              {label}
            </span>
            <span className="text-[0.65rem] text-[var(--muted)]">
              · {task.capability}
            </span>
          </div>
        </div>
        <span
          className={`flex shrink-0 items-center gap-1 text-[0.65rem] ${statusConfig.tone}`}
        >
          {React.createElement(statusConfig.icon, {
            className: `size-3 ${statusConfig.spin ? "animate-spin" : ""}`,
          })}
          {statusConfig.label}
        </span>
        {hasDetails ? (
          <ChevronDown
            className={`size-3 shrink-0 text-[var(--muted)] transition-transform duration-200 ${
              expanded ? "rotate-180" : ""
            }`}
          />
        ) : null}
      </button>

      {/* Expandable details */}
      {expanded ? (
        <div className="border-t border-[var(--hairline)] bg-[var(--canvas-soft)]/20">
          {task.inputSummary ? (
            <div className="px-3 py-2">
              <p className="text-[0.6rem] font-medium uppercase tracking-wide text-[var(--muted)]">
                输入
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                {task.inputSummary}
              </p>
            </div>
          ) : null}

          {/* Output on success */}
          {task.status === "completed" && task.output ? (
            <div className="border-t border-[var(--hairline)] px-3 py-2">
              <p className="text-[0.6rem] font-medium uppercase tracking-wide text-[var(--muted)]">
                结果
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                {formatOutput(task.output)}
              </p>
            </div>
          ) : null}

          {/* Error + retry on failure */}
          {task.status === "failed" ? (
            <div className="flex items-center justify-between px-3 py-2">
              <span className="flex items-center gap-1.5 text-xs text-[var(--danger)]">
                <AlertTriangle className="size-3" />
                {task.errorDetail ?? "执行失败"}
              </span>
              {task.onRetry ? (
                <button
                  className="flex items-center gap-1 rounded px-2 py-0.5 text-xs text-[var(--primary)] transition-colors hover:bg-[var(--primary)]/10"
                  onClick={() => task.onRetry?.(task.taskId)}
                  type="button"
                >
                  <RefreshCw className="size-3" />
                  重试
                </button>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

const STATUS_MAP: Record<
  string,
  { label: string; icon: typeof CheckCircle2; tone: string; spin: boolean }
> = {
  delegated: {
    label: "已委派",
    icon: Loader2,
    tone: "text-[var(--muted)]",
    spin: false,
  },
  running: {
    label: "执行中",
    icon: Loader2,
    tone: "text-[var(--primary)]",
    spin: true,
  },
  completed: {
    label: "已完成",
    icon: CheckCircle2,
    tone: "text-[var(--success)]",
    spin: false,
  },
  failed: {
    label: "失败",
    icon: XCircle,
    tone: "text-[var(--danger)]",
    spin: false,
  },
};

function formatOutput(output: Record<string, unknown>): string {
  const artifacts = output.artifacts;
  if (Array.isArray(artifacts) && artifacts.length > 0) {
    const types = artifacts
      .map((a: Record<string, unknown>) => String(a.type ?? ""))
      .filter(Boolean);
    return `创建了 ${types.length} 个资产：${types.join("、")}`;
  }
  const message = output.message;
  if (typeof message === "string") return message;
  return "操作完成";
}
