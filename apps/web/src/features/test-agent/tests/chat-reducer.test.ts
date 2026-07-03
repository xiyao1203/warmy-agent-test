import { describe, expect, it } from "vitest";

import type { AgentEvent, ChatResponse } from "../api";
import { chatReducer, initialChatState } from "../chat-reducer";

const snapshot: ChatResponse = {
  session_id: "session-1",
  title: "Chat",
  status: "active",
  updated_at: "2026-07-03T00:00:00Z",
  messages: [],
  artifacts: [],
  protocol_version: 2,
  plan_draft: {},
  timeline: [
    {
      kind: "event",
      id: "event-7",
      timestamp: "2026-07-03T00:00:00Z",
      event_type: "generation.started",
      event_sequence: 7,
      generation_id: "generation-1",
      payload: {},
    },
  ],
  event_cursor: 7,
  active_generation: {
    generation_id: "generation-1",
    status: "running",
    partial_content: "",
    workflow_id: "workflow-1",
  },
};

describe("chat reducer recovery", () => {
  it("loads the server timeline, cursor and active generation", () => {
    const state = chatReducer(initialChatState(), {
      type: "APPLY_SESSION",
      session: snapshot,
    });

    expect(state.timeline).toEqual(snapshot.timeline);
    expect(state.eventCursor).toBe(7);
    expect(state.activeGeneration?.status).toBe("running");
  });

  it("ignores duplicate events and advances the cursor", () => {
    const loaded = chatReducer(initialChatState(), {
      type: "APPLY_SESSION",
      session: snapshot,
    });
    const duplicate: AgentEvent = {
      id: 7,
      type: "generation.started",
      payload: {},
    };
    const next: AgentEvent = {
      id: 8,
      type: "agent.progress",
      payload: { task_id: "task-1" },
    };

    const unchanged = chatReducer(loaded, {
      type: "ADD_EVENT",
      event: duplicate,
    });
    const advanced = chatReducer(unchanged, { type: "ADD_EVENT", event: next });

    expect(unchanged.events).toHaveLength(0);
    expect(advanced.events).toHaveLength(1);
    expect(advanced.eventCursor).toBe(8);
  });
});
