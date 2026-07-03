"use client";

import { Brain } from "lucide-react";

export function ReasoningBlock({
  step,
  total,
  capability,
  isStreaming,
}: {
  content: string;
  step?: number;
  total?: number;
  capability?: string;
  isStreaming?: boolean;
}) {
  const hasStep = step !== undefined && total !== undefined && total > 0;
  const label = isStreaming
    ? "正在分析请求…"
    : hasStep
      ? `已分析请求 · ${step}/${total}`
      : "已分析请求";

  return (
    <div
      className="flex min-h-9 items-center gap-2 border-l border-[var(--hairline-strong)] py-1 pl-4 text-xs text-[var(--muted)]"
      role="status"
    >
      <Brain
        aria-hidden="true"
        className={`size-3.5 shrink-0 ${isStreaming ? "animate-pulse" : ""}`}
      />
      <span>{label}</span>
      {capability ? (
        <span className="truncate text-[var(--muted)]/70">{capability}</span>
      ) : null}
    </div>
  );
}
