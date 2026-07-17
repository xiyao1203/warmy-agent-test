import type { TaskState } from "@/components/uiverse";

import type { AgentEvent } from "./api";

export function buildTaskStates(events: AgentEvent[]): TaskState[] {
  const groups = new Map<
    string,
    { delegated: AgentEvent | null; latest: AgentEvent }
  >();
  const order: string[] = [];
  for (const event of events) {
    if (
      ![
        "agent.delegated",
        "agent.progress",
        "agent.completed",
        "agent.failed",
      ].includes(event.type)
    ) {
      continue;
    }
    const taskId = String(event.payload.task_id ?? "");
    if (!taskId) continue;
    if (!groups.has(taskId)) order.push(taskId);
    const existing = groups.get(taskId);
    if (!existing) {
      groups.set(taskId, { delegated: null, latest: event });
    } else {
      existing.latest = event;
    }
    if (event.type === "agent.delegated") {
      groups.get(taskId)!.delegated = event;
    }
  }
  return order.map((taskId) => {
    const group = groups.get(taskId)!;
    const statusMap: Record<string, TaskState["status"]> = {
      "agent.delegated": "delegated",
      "agent.progress": "running",
      "agent.completed": "completed",
      "agent.failed": "failed",
    };
    return {
      taskId,
      childAgent: group.delegated
        ? String(group.delegated.payload.child_agent ?? "")
        : String(group.latest.payload.child_agent ?? ""),
      capability: group.delegated
        ? String(group.delegated.payload.capability ?? "")
        : String(group.latest.payload.capability ?? ""),
      inputSummary: group.delegated
        ? String(group.delegated.payload.input_summary ?? "")
        : "",
      status: statusMap[group.latest.type] ?? "delegated",
      output:
        group.latest.type === "agent.completed"
          ? ((group.latest.payload.output as Record<string, unknown> | null) ??
            null)
          : null,
      errorDetail:
        group.latest.type === "agent.failed"
          ? String(group.latest.payload.detail ?? null)
          : null,
    };
  });
}

export function getTimeGapMinutes(a: string, b: string): number {
  const first = new Date(a).getTime();
  const second = new Date(b).getTime();
  if (Number.isNaN(first) || Number.isNaN(second)) return 0;
  return Math.abs(second - first) / 60_000;
}

export function formatRelativeDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const diffMin = Math.floor((Date.now() - date.getTime()) / 60_000);
  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin} 分钟前`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr} 小时前`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay} 天前`;
  return date.toLocaleDateString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
