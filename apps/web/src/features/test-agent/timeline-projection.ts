import type { TimelineItem } from "./api";

export type ToolTimelineItem = {
  kind: "tool";
  id: string;
  taskId: string;
  label: string;
  summary: string;
  status: "queued" | "running" | "completed" | "failed";
  details: Record<string, unknown>;
};

export type ConversationItem = TimelineItem | ToolTimelineItem;

const TOOL_EVENTS = new Set([
  "agent.delegated",
  "agent.progress",
  "agent.completed",
  "agent.failed",
]);

export function projectTimeline(items: TimelineItem[]): ConversationItem[] {
  const projected: ConversationItem[] = [];
  const tools = new Map<string, ToolTimelineItem>();

  for (const item of items) {
    if (item.kind !== "event" || !TOOL_EVENTS.has(item.event_type)) {
      projected.push(item);
      continue;
    }

    const taskId = String(item.payload.task_id ?? "");
    if (!taskId) {
      projected.push(item);
      continue;
    }

    const existing = tools.get(taskId);
    const next = toolItem(item, existing);
    if (existing) Object.assign(existing, next);
    else {
      tools.set(taskId, next);
      projected.push(next);
    }
  }

  return projected;
}

function toolItem(
  item: Extract<TimelineItem, { kind: "event" }>,
  existing?: ToolTimelineItem,
): ToolTimelineItem {
  const capability = String(
    item.payload.capability ??
      existing?.details.capability ??
      item.payload.child_agent ??
      "工具",
  );
  const status = statusFor(item.event_type);
  const summary = String(
    item.payload.output_summary ??
      item.payload.detail ??
      item.payload.input_summary ??
      existing?.summary ??
      "",
  );
  return {
    kind: "tool",
    id: `tool-${String(item.payload.task_id)}`,
    taskId: String(item.payload.task_id),
    status,
    label: labelFor(capability, status),
    summary,
    details: { ...(existing?.details ?? {}), ...item.payload, capability },
  };
}

function statusFor(eventType: string): ToolTimelineItem["status"] {
  if (eventType === "agent.progress") return "running";
  if (eventType === "agent.completed") return "completed";
  if (eventType === "agent.failed") return "failed";
  return "queued";
}

function labelFor(
  capability: string,
  status: ToolTimelineItem["status"],
): string {
  if (status === "running") return `正在调用 ${capability}`;
  if (status === "completed") return `${capability} 已完成`;
  if (status === "failed") return `${capability} 失败`;
  return `准备调用 ${capability}`;
}
