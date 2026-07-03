import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import type { TimelineItem } from "../api";
import { ConversationTimeline } from "../conversation-timeline";

test("renders server timeline items in their supplied order", () => {
  const items: TimelineItem[] = [
    {
      kind: "message",
      id: "m1",
      timestamp: "2026-07-03T00:00:00Z",
      role: "user",
      content: "运行登录测试",
      sequence: 1,
    },
    {
      kind: "event",
      id: "e1",
      timestamp: "2026-07-03T00:00:01Z",
      event_type: "agent.reasoning",
      event_sequence: 2,
      generation_id: "g1",
      payload: { content: "先检查测试计划" },
    },
    {
      kind: "event",
      id: "e2",
      timestamp: "2026-07-03T00:00:02Z",
      event_type: "agent.progress",
      event_sequence: 3,
      generation_id: "g1",
      payload: { capability: "run_plan" },
    },
    {
      kind: "message",
      id: "m2",
      timestamp: "2026-07-03T00:00:03Z",
      role: "assistant",
      content: "测试已启动",
      sequence: 2,
    },
  ];

  render(<ConversationTimeline items={items} />);

  expect(
    screen.getAllByTestId("timeline-item").map((node) => node.dataset.kind),
  ).toEqual(["user-message", "reasoning", "tool", "assistant-message"]);
});

test("shows a cancelled generation as stopped", () => {
  const items: TimelineItem[] = [
    {
      kind: "event",
      id: "e1",
      timestamp: "2026-07-03T00:00:00Z",
      event_type: "generation.cancelled",
      event_sequence: 1,
      generation_id: "g1",
      payload: { content: "partial" },
    },
  ];

  render(<ConversationTimeline items={items} />);
  expect(screen.getByText("已停止")).toBeVisible();
});
