import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildTaskStates,
  formatRelativeDate,
  getTimeGapMinutes,
} from "../chat-workspace-model";
import type { AgentEvent } from "../api";

function event(
  id: number,
  type: AgentEvent["type"],
  payload: Record<string, unknown>,
): AgentEvent {
  return { id, type, payload };
}

describe("chat workspace model", () => {
  afterEach(() => vi.useRealTimers());

  it("projects delegated tasks in stable order with their latest state", () => {
    const states = buildTaskStates([
      event(1, "agent.delegated", {
        task_id: "task-1",
        child_agent: "API Agent",
        capability: "agents.create",
        input_summary: "创建接口 Agent",
      }),
      event(2, "agent.delegated", {
        task_id: "task-2",
        child_agent: "Run Agent",
        capability: "runs.create",
      }),
      event(3, "agent.completed", {
        task_id: "task-1",
        output: { id: "agent-1" },
      }),
    ]);

    expect(states.map(({ taskId, status }) => ({ taskId, status }))).toEqual([
      { taskId: "task-1", status: "completed" },
      { taskId: "task-2", status: "delegated" },
    ]);
    expect(states[0].output).toEqual({ id: "agent-1" });
  });

  it("formats relative dates and handles invalid timestamps", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-17T12:00:00.000Z"));

    expect(formatRelativeDate("2026-07-17T11:45:00.000Z")).toBe("15 分钟前");
    expect(formatRelativeDate("not-a-date")).toBe("");
    expect(
      getTimeGapMinutes("2026-07-17T11:00:00.000Z", "2026-07-17T11:30:00.000Z"),
    ).toBe(30);
  });
});
