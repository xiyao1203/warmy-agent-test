import { describe, expect, it } from "vitest";

import type { TimelineItem } from "../api";
import { projectTimeline } from "../timeline-projection";

const event = (
  id: string,
  sequence: number,
  eventType: string,
  payload: Record<string, unknown>,
): TimelineItem => ({
  kind: "event",
  id,
  timestamp: `2026-07-03T00:00:0${sequence}Z`,
  event_type: eventType,
  event_sequence: sequence,
  generation_id: "generation-1",
  payload,
});

describe("projectTimeline", () => {
  it("merges one tool lifecycle into a single item at its first position", () => {
    const items: TimelineItem[] = [
      event("delegated", 1, "agent.delegated", {
        task_id: "task-1",
        capability: "run_plan",
        input_summary: "执行登录回归计划",
      }),
      event("progress", 2, "agent.progress", {
        task_id: "task-1",
        capability: "run_plan",
      }),
      event("completed", 3, "agent.completed", {
        task_id: "task-1",
        capability: "run_plan",
        output_summary: "12 项通过",
      }),
    ];

    expect(projectTimeline(items)).toEqual([
      expect.objectContaining({
        kind: "tool",
        id: "tool-task-1",
        status: "completed",
        label: "run_plan 已完成",
        summary: "12 项通过",
      }),
    ]);
  });

  it("preserves confirmation and cancellation positions", () => {
    const confirmation = event(
      "confirmation",
      1,
      "tool.confirmation_required",
      {
        confirmation_id: "confirmation-1",
      },
    );
    const cancellation = event("cancelled", 2, "generation.cancelled", {
      content: "部分回答",
    });

    expect(projectTimeline([confirmation, cancellation])).toEqual([
      confirmation,
      cancellation,
    ]);
  });
});
