"use client";

import {
  CheckCircle2,
  ChevronDown,
  CircleDashed,
  Clock3,
  Loader2,
  OctagonX,
  Wrench,
  XCircle,
} from "lucide-react";
import { useState } from "react";

import { MarkdownContent, ReasoningBlock } from "@/components/uiverse";

import type { TimelineItem } from "./api";
import {
  projectTimeline,
  type ToolTimelineItem,
} from "./timeline-projection";

export function ConversationTimeline({ items }: { items: TimelineItem[] }) {
  return (
    <div className="space-y-6">
      {projectTimeline(items).map((item) => {
        if (item.kind === "tool") {
          return <ToolProcessRow item={item} key={item.id} />;
        }
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

function ToolProcessRow({ item }: { item: ToolTimelineItem }) {
  const [expanded, setExpanded] = useState(false);
  const config = {
    queued: { icon: CircleDashed, tone: "text-[var(--muted)]" },
    running: { icon: Loader2, tone: "text-[var(--primary)]" },
    completed: { icon: CheckCircle2, tone: "text-[var(--success)]" },
    failed: { icon: XCircle, tone: "text-[var(--danger)]" },
  }[item.status];
  const Icon = config.icon;
  const details = Object.entries(item.details).filter(
    ([key]) =>
      ![
        "task_id",
        "capability",
        "child_agent",
        "input_summary",
        "output_summary",
      ].includes(key),
  );
  const expandable = Boolean(item.summary || details.length > 0);

  return (
    <div
      className="border-l border-[var(--hairline-strong)] py-0.5 pl-4"
      data-kind="tool"
      data-testid="timeline-item"
    >
      <button
        aria-expanded={expandable ? expanded : undefined}
        className="group flex min-h-9 w-full items-start gap-3 rounded-lg py-1.5 pr-2 text-left hover:bg-[var(--canvas-soft)]"
        disabled={!expandable}
        onClick={() => expandable && setExpanded((value) => !value)}
        type="button"
      >
        <Icon
          className={`mt-0.5 size-4 shrink-0 ${config.tone} ${item.status === "running" ? "animate-spin" : ""}`}
        />
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-medium text-[var(--ink)]">
            {item.label}
          </span>
          {item.summary ? (
            <span className="mt-0.5 block truncate text-xs leading-5 text-[var(--muted)]">
              {item.summary}
            </span>
          ) : null}
        </span>
        {expandable ? (
          <ChevronDown
            aria-hidden="true"
            className={`mt-0.5 size-4 shrink-0 text-[var(--muted)] transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        ) : null}
      </button>
      {expanded ? (
        <div className="ml-7 mt-1 rounded-lg bg-[var(--canvas-soft)] px-3 py-2 text-xs leading-5 text-[var(--muted)]">
          {item.summary ? <p>{item.summary}</p> : null}
          {details.length > 0 ? (
            <dl className="mt-1.5 grid gap-1">
              {details.map(([key, value]) => (
                <div className="grid grid-cols-[7rem_minmax(0,1fr)] gap-2" key={key}>
                  <dt className="font-mono text-[var(--body)]">{key}</dt>
                  <dd className="break-words">
                    {typeof value === "object"
                      ? JSON.stringify(value)
                      : String(value)}
                  </dd>
                </div>
              ))}
            </dl>
          ) : null}
        </div>
      ) : null}
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
