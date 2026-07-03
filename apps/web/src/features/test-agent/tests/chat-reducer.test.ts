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

    expect(unchanged.events).toHaveLength(1);
    expect(advanced.events).toHaveLength(2);
    expect(advanced.eventCursor).toBe(8);
  });

  it("commits a streamed assistant response once when the request is aborted", () => {
    const streaming = {
      ...initialChatState(),
      streamingContent: "已完成一半",
      streamingActive: true,
    };

    const committed = chatReducer(streaming, {
      type: "COMMIT_STREAMING_MESSAGE",
      eventId: 9,
      content: "已完成一半",
      timestamp: "2026-07-03T00:00:01Z",
    });
    const duplicate = chatReducer(committed, {
      type: "COMMIT_STREAMING_MESSAGE",
      eventId: 9,
      content: "已完成一半",
      timestamp: "2026-07-03T00:00:01Z",
    });

    expect(committed.messages).toEqual([
      expect.objectContaining({ role: "assistant", content: "已完成一半" }),
    ]);
    expect(committed.streamingContent).toBe("");
    expect(committed.streamingActive).toBe(false);
    expect(duplicate.messages).toHaveLength(1);
  });

  it("reconciles the server completion with an optimistic stopped response", () => {
    const optimistic = chatReducer(initialChatState(), {
      type: "APPEND_MESSAGE",
      message: {
        role: "assistant",
        content: "已完成一半",
        timestamp: "2026-07-03T00:00:00Z",
      },
    });

    const reconciled = chatReducer(optimistic, {
      type: "COMMIT_STREAMING_MESSAGE",
      eventId: 10,
      content: "已完成一半",
      timestamp: "2026-07-03T00:00:01Z",
    });

    expect(reconciled.messages).toHaveLength(1);
  });
});
