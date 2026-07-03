import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import { TestAgentChat } from "../chat-screen";

const { listSessions, createSession, getSession, sendChatMessage } = vi.hoisted(
  () => ({
    listSessions: vi.fn(),
    createSession: vi.fn(),
    getSession: vi.fn(),
    sendChatMessage: vi.fn(),
  }),
);

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    listSessions,
    createSession,
    getSession,
    sendChatMessage,
    subscribeToSession: vi.fn((_projectId, _sessionId, onEvent) => {
      queueMicrotask(() =>
        onEvent({ id: 0, type: "stream.ready", payload: { cursor: 0 } }),
      );
      return () => undefined;
    }),
  };
});

beforeEach(() => {
  vi.clearAllMocks();
  Element.prototype.scrollTo = vi.fn();
  window.history.replaceState({}, "", "/projects/project-1/test-agent");
  listSessions.mockResolvedValue({
    items: [
      {
        session_id: "session-1",
        title: "登录回归",
        status: "active",
        updated_at: "2026-06-30T00:00:00Z",
      },
    ],
  });
  createSession.mockResolvedValue({
    session_id: "session-2",
    title: "新对话",
    status: "active",
    updated_at: "2026-06-30T00:00:00Z",
    messages: [],
    artifacts: [],
    protocol_version: 2,
    plan_draft: {},
  });
  getSession.mockResolvedValue({
    session_id: "session-1",
    title: "登录回归",
    status: "active",
    updated_at: "2026-06-30T00:00:00Z",
    messages: [
      { role: "user", content: "测试登录", timestamp: "2026-06-30T00:00:00Z" },
      {
        role: "assistant",
        content: "请选择 Agent 版本",
        timestamp: "2026-06-30T00:00:01Z",
      },
    ],
    artifacts: [],
    protocol_version: 2,
    plan_draft: {},
  });
});

test("restores a persisted session from project history", async () => {
  render(<TestAgentChat projectId="project-1" />);

  expect(await screen.findByText("登录回归")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "登录回归" }));

  expect(await screen.findByText("请选择 Agent 版本")).toBeVisible();
  expect(getSession).toHaveBeenCalledWith("project-1", "session-1");
  expect(window.location.search).toBe("?session=session-1");
});

test("creates a durable session before the first message", async () => {
  sendChatMessage.mockResolvedValue({
    session_id: "session-2",
    title: "你好",
    status: "active",
    updated_at: "2026-06-30T00:00:01Z",
    messages: [
      { role: "user", content: "你好", timestamp: "2026-06-30T00:00:00Z" },
      {
        role: "assistant",
        content: "你想测试哪个 Agent？",
        timestamp: "2026-06-30T00:00:01Z",
      },
    ],
    artifacts: [],
    protocol_version: 2,
    plan_draft: {},
  });
  render(<TestAgentChat projectId="project-1" />);

  fireEvent.change(screen.getByPlaceholderText(/向超级测试 Agent 描述目标/), {
    target: { value: "你好" },
  });
  fireEvent.click(screen.getByRole("button", { name: /发送/ }));

  await waitFor(() => expect(createSession).toHaveBeenCalledWith("project-1"));
  expect(sendChatMessage).toHaveBeenCalledWith(
    "project-1",
    "session-2",
    "你好",
    expect.any(String),
    expect.anything(),
  );
  expect(await screen.findByText("你想测试哪个 Agent？")).toBeVisible();
});

test("renders the refined composer and panel controls", async () => {
  render(<TestAgentChat projectId="project-1" />);

  expect(
    screen.getByPlaceholderText("向超级测试 Agent 描述目标…"),
  ).toBeVisible();
  expect(screen.getByText("Enter 发送 · Shift+Enter 换行")).toBeVisible();
  expect(screen.getByRole("button", { name: "关闭会话历史" })).toBeVisible();
  expect(screen.getByRole("button", { name: "打开上下文" })).toBeVisible();
  expect(await screen.findByText("登录回归")).toBeVisible();
});
