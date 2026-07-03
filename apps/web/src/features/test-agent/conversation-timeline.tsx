"use client";

import {
  CheckCircle2,
  CircleDashed,
  Clock3,
  Loader2,
  OctagonX,
  Wrench,
  XCircle,
} from "lucide-react";

import { MarkdownContent, ReasoningBlock } from "@/components/uiverse";

import type { TimelineItem } from "./api";

export function ConversationTimeline({ items }: { items: TimelineItem[] }) {
  return (
    <div className="space-y-6">
      {items.map((item) => {
        if (item.kind === "message") {
          return (
            <article
              className={
                item.role === "user" ? "flex justify-end" : "max-w-none"
              }
              data-kind={`${item.role}-message`}
              data-testid="timeline-item"
              key={item.id}
            >
              {item.role === "user" ? (
                <div className="max-w-[80%] rounded-3xl bg-[var(--canvas-soft)] px-4 py-2.5 text-[0.9375rem] leading-6 text-[var(--ink)]">
                  {item.content}
                </div>
              ) : (
                <div className="px-1 text-[0.9375rem] leading-7 text-[var(--ink)]">
                  <MarkdownContent content={item.content} />
                </div>
              )}
            </article>
          );
        }

        if (item.event_type === "agent.reasoning") {
          return (
            <div
              data-kind="reasoning"
              data-testid="timeline-item"
              key={item.id}
            >
              <ReasoningBlock
                capability={String(item.payload.capability ?? "")}
                content={String(item.payload.content ?? "")}
                step={Number(item.payload.step ?? 0)}
                total={Number(item.payload.total ?? 0)}
              />
            </div>
          );
        }

        if (item.event_type === "generation.cancelled") {
          return (
            <ProcessRow
              detail={String(item.payload.content ?? "")}
              icon={OctagonX}
              kind="status"
              key={item.id}
              label="已停止"
              tone="text-[var(--muted)]"
            />
          );
        }

        const process = processView(item.event_type, item.payload);
        if (!process) return null;
        return <ProcessRow key={item.id} {...process} />;
      })}
    </div>
  );
}

function ProcessRow({
  label,
  detail,
  tone,
  icon: Icon,
  spin = false,
  kind = "tool",
}: {
  label: string;
  detail: string;
  tone: string;
  icon: typeof Wrench;
  spin?: boolean;
  kind?: string;
}) {
  return (
    <div
      className="flex items-start gap-3 border-l border-[var(--hairline-strong)] py-1 pl-4"
      data-kind={kind}
      data-testid="timeline-item"
    >
      <Icon
        className={`mt-0.5 size-4 shrink-0 ${tone} ${spin ? "animate-spin" : ""}`}
      />
      <div className="min-w-0">
        <p className="text-sm font-medium text-[var(--ink)]">{label}</p>
        {detail ? (
          <p className="mt-0.5 break-words text-xs leading-5 text-[var(--muted)]">
            {detail}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function processView(eventType: string, payload: Record<string, unknown>) {
  const capability = String(
    payload.capability ?? payload.child_agent ?? "工具",
  );
  if (eventType === "agent.delegated") {
    return {
      label: `准备调用 ${capability}`,
      detail: String(payload.input_summary ?? ""),
      tone: "text-[var(--muted)]",
      icon: CircleDashed,
    };
  }
  if (eventType === "agent.progress") {
    return {
      label: `正在调用 ${capability}`,
      detail: "",
      tone: "text-[var(--primary)]",
      icon: Loader2,
      spin: true,
    };
  }
  if (eventType === "tool.confirmation_required") {
    return {
      label: "等待确认",
      detail: capability,
      tone: "text-[var(--warning)]",
      icon: Clock3,
    };
  }
  if (eventType === "agent.completed") {
    return {
      label: `${capability} 已完成`,
      detail: "",
      tone: "text-[var(--success)]",
      icon: CheckCircle2,
    };
  }
  if (eventType === "agent.failed" || eventType === "error") {
    return {
      label: `${capability} 失败`,
      detail: String(payload.detail ?? "执行失败"),
      tone: "text-[var(--danger)]",
      icon: XCircle,
    };
  }
  return null;
}
