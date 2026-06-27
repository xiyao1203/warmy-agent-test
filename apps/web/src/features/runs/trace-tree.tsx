"use client";

import { ChevronRight, Clock, Cpu, Zap } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";

export type TraceSpan = {
  id?: string;
  name?: string;
  event_type?: string;
  duration_ms?: number | null;
  token_count?: number | null;
  cost?: number | null;
  parent_event_id?: string | null;
  status?: string;
  payload?: Record<string, unknown>;
  children?: TraceSpan[];
};

type TraceTreeNodeProps = {
  depth?: number;
  span: TraceSpan;
};

const TYPE_COLORS: Record<string, string> = {
  error: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  model_request: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  result: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  step: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  tool_call: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
};

function TraceTreeNode({ depth = 0, span }: TraceTreeNodeProps) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = (span.children?.length ?? 0) > 0;
  const typeKey = span.event_type ?? "step";
  const colorClass = TYPE_COLORS[typeKey] ?? TYPE_COLORS.step;

  return (
    <div className={depth > 0 ? "ml-5 border-l border-[var(--border)] pl-3" : ""}>
      <button
        className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm hover:bg-[var(--surface-subtle)]"
        onClick={() => hasChildren && setExpanded(!expanded)}
        type="button"
      >
        {hasChildren ? (
          <ChevronRight
            aria-hidden="true"
            className={`size-3.5 shrink-0 transition-transform ${expanded ? "rotate-90" : ""}`}
          />
        ) : (
          <span className="w-3.5" />
        )}
        <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${colorClass}`}>
          {typeKey}
        </span>
        <span className="flex-1 truncate font-medium">
          {span.name ?? span.id ?? `span-${depth}`}
        </span>
        <span className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          {span.duration_ms != null ? (
            <span className="flex items-center gap-0.5">
              <Clock aria-hidden="true" className="size-3" />
              {span.duration_ms}ms
            </span>
          ) : null}
          {span.token_count != null ? (
            <span className="flex items-center gap-0.5">
              <Cpu aria-hidden="true" className="size-3" />
              {span.token_count}
            </span>
          ) : null}
          {span.cost != null ? (
            <span className="flex items-center gap-0.5">
              <Zap aria-hidden="true" className="size-3" />
              ¥{span.cost.toFixed(2)}
            </span>
          ) : null}
        </span>
        {span.status ? (
          <Badge
            tone={
              span.status === "passed" || span.status === "ok"
                ? "success"
                : span.status === "error"
                  ? "danger"
                  : "neutral"
            }
          >
            {span.status}
          </Badge>
        ) : null}
      </button>
      {expanded && hasChildren ? (
        <div className="mt-1 space-y-0.5">
          {span.children!.map((child, i) => (
            <TraceTreeNode depth={depth + 1} key={child.id ?? i} span={child} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** 将扁平 span 列表构建为树结构 */
function buildTree(spans: TraceSpan[]): TraceSpan[] {
  const map = new Map<string, TraceSpan>();
  for (const span of spans) {
    map.set(span.id ?? "", { ...span, children: [] });
  }
  const roots: TraceSpan[] = [];
  for (const span of spans) {
    const node = map.get(span.id ?? "")!;
    const parentId = span.parent_event_id;
    if (parentId && map.has(parentId)) {
      map.get(parentId)!.children!.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
}

export function TraceTree({ spans }: { spans: TraceSpan[] }) {
  if (spans.length === 0) {
    return (
      <div className="rounded border border-dashed border-[var(--border)] p-6 text-center text-sm text-[var(--text-muted)]">
        暂无 Trace 数据
      </div>
    );
  }

  const tree = buildTree(spans);

  return (
    <div className="space-y-0.5 rounded border border-[var(--border)] bg-[var(--surface)] p-2">
      {tree.map((span, i) => (
        <TraceTreeNode key={span.id ?? i} span={span} />
      ))}
    </div>
  );
}

export function TraceTimeline({ spans }: { spans: TraceSpan[] }) {
  if (spans.length === 0) return null;

  const maxDuration = Math.max(
    ...spans.map((s) => s.duration_ms ?? 0),
    1,
  );

  return (
    <div className="space-y-1">
      {spans.map((span, i) => {
        const typeKey = span.event_type ?? "step";
        const colorClass = TYPE_COLORS[typeKey] ?? TYPE_COLORS.step;
        const pct = maxDuration > 0 ? ((span.duration_ms ?? 0) / maxDuration) * 100 : 0;

        return (
          <div className="flex items-center gap-3 text-xs" key={span.id ?? i}>
            <span className="w-24 truncate text-right text-[var(--text-muted)]">
              {span.name ?? `span-${i}`}
            </span>
            <div className="flex-1">
              <div
                className={`h-5 rounded ${colorClass} flex items-center px-2`}
                style={{ width: `${Math.max(pct, 2)}%`, minWidth: "2rem" }}
              >
                <span className="truncate text-[10px] font-medium">
                  {span.duration_ms != null ? `${span.duration_ms}ms` : ""}
                </span>
              </div>
            </div>
            <span className="w-16 text-right text-[var(--text-muted)]">
              {span.token_count != null ? `${span.token_count} tok` : ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}
