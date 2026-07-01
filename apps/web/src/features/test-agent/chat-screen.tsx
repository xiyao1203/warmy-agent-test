"use client";

import { Bot, Send, Sparkles, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatEmptyState, TypingIndicator } from "@/components/uiverse";

import {
  createSession,
  deleteSession,
  getSession,
  listSessions,
  sendChatMessage,
  subscribeToSession,
  TestAgentApiError,
} from "./api";
import type {
  AgentEvent,
  ArtifactLink,
  ChatMessage,
  ChatResponse,
  SessionSummary,
} from "./api";
import { ContextPanel } from "./context-panel";
import { ConfirmationCard } from "./confirmation-card";
import { SessionList } from "./session-list";
import { TargetChatScreen } from "./target-chat-screen";

export function TestAgentChat({ projectId }: { projectId: string }) {
  const [workspace, setWorkspace] = useState<"super" | "target">("super");
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [active, setActive] = useState<ChatResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactLink[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [input, setInput] = useState("");
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const activeSessionId = active?.session_id ?? null;

  useEffect(() => {
    let alive = true;
    const requested = new URLSearchParams(window.location.search).get(
      "session",
    );
    listSessions(projectId)
      .then(async (response) => {
        if (!alive) return;
        setSessions(response.items);
        if (requested) {
          const session = await getSession(projectId, requested);
          if (!alive) return;
          applySession(session);
        }
      })
      .catch((reason: unknown) => {
        if (alive)
          setError(
            reason instanceof Error ? reason.message : "会话历史加载失败",
          );
      })
      .finally(() => {
        if (alive) setLoadingHistory(false);
      });
    return () => {
      alive = false;
    };
  }, [projectId]);

  useEffect(() => {
    if (!activeSessionId) return;
    return subscribeToSession(projectId, activeSessionId, (event) => {
      setEvents((current) =>
        current.some((item) => item.id === event.id && item.type === event.type)
          ? current
          : [...current, event],
      );
      if (event.type === "asset.created") {
        const next = {
          type: String(event.payload.type),
          id: String(event.payload.id),
          relation: String(event.payload.relation ?? "created"),
        };
        setArtifacts((current) =>
          current.some((item) => item.type === next.type && item.id === next.id)
            ? current
            : [...current, next],
        );
      }
      if (event.type === "message.started") setStreamingContent("");
      if (event.type === "message.delta") {
        setStreamingContent(
          (current) => current + String(event.payload.content ?? ""),
        );
      }
      if (event.type === "message.completed") setStreamingContent("");
    });
  }, [activeSessionId, projectId]);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, sending]);

  function applySession(session: ChatResponse) {
    setActive(session);
    setMessages(session.messages);
    setArtifacts(session.artifacts);
    setEvents([]);
    window.history.replaceState(
      {},
      "",
      `${window.location.pathname}?session=${session.session_id}`,
    );
  }

  async function selectSession(sessionId: string) {
    setError(null);
    try {
      applySession(await getSession(projectId, sessionId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "会话加载失败");
    }
  }

  async function newSession() {
    setError(null);
    const session = await createSession(projectId);
    applySession(session);
    setSessions((current) => [session, ...current]);
    return session;
  }

  async function handleDelete(sessionId: string) {
    try {
      const response = await deleteSession(projectId, sessionId);
      if (!response.ok) throw new Error("删除失败");
      setSessions((current) =>
        current.filter((item) => item.session_id !== sessionId),
      );
      if (activeSessionId === sessionId) {
        setActive(null);
        setMessages([]);
        setArtifacts([]);
        setEvents([]);
        window.history.replaceState({}, "", window.location.pathname);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "删除会话失败");
    }
  }

  async function handleSend() {
    const content = input.trim();
    if (!content || sending) return;
    setInput("");
    setSending(true);
    setError(null);
    try {
      const session = active ?? (await newSession());
      const response = await sendChatMessage(
        projectId,
        session.session_id,
        content,
      );
      applySession(response);
      setSessions((current) => [
        response,
        ...current.filter((item) => item.session_id !== response.session_id),
      ]);
    } catch (reason) {
      setInput(content);
      setError(
        reason instanceof TestAgentApiError || reason instanceof Error
          ? reason.message
          : "对话失败，请重试。",
      );
    } finally {
      setSending(false);
    }
  }

  if (workspace === "target") {
    return (
      <div className="flex h-full flex-col">
        <WorkspaceTabs value={workspace} onChange={setWorkspace} />
        <TargetChatScreen projectId={projectId} />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <WorkspaceTabs value={workspace} onChange={setWorkspace} />
      <div className="min-h-0 flex-1 grid grid-cols-[16rem_minmax(0,1fr)_19rem] max-[1100px]:grid-cols-[14rem_minmax(0,1fr)] max-[760px]:grid-cols-1">
        <SessionList
          activeId={active?.session_id ?? null}
          items={sessions}
          loading={loadingHistory}
          onCreate={() => void newSession()}
          onDelete={(id) => void handleDelete(id)}
          onSelect={(id) => void selectSession(id)}
        />

        <main className="flex min-h-0 min-w-0 flex-col bg-[var(--canvas)]">
          <header className="flex items-center gap-3 border-b border-[var(--hairline)] px-5 py-3">
            <Sparkles className="size-5 text-[var(--primary)]" />
            <div>
              <h1 className="text-sm font-semibold">超级测试 Agent</h1>
              <p className="text-xs text-[var(--muted)]">
                编排被测智能体、用例、执行、评测、安全与发布门禁
              </p>
            </div>
          </header>

          <div
            className="min-h-0 flex-1 overflow-y-auto px-5 py-4"
            ref={scrollRef}
          >
            {messages.length === 0 ? (
              <ChatEmptyState
                onSuggestionClick={setInput}
                suggestions={[
                  "测试 Agent v2.3 并与 v2.2 做实验对比",
                  "为登录场景生成回归用例和测试计划",
                  "执行安全红队测试并评估发布门禁",
                ]}
              />
            ) : (
              <div className="mx-auto max-w-3xl space-y-4">
                {messages.map((message, index) => (
                  <MessageBubble
                    key={`${message.timestamp}:${index}`}
                    message={message}
                  />
                ))}
                {streamingContent ? (
                  <MessageBubble
                    message={{
                      role: "assistant",
                      content: streamingContent,
                      timestamp: "streaming",
                    }}
                  />
                ) : null}
                {active
                  ? events
                      .filter(
                        (event) => event.type === "tool.confirmation_required",
                      )
                      .map((event) => (
                        <ConfirmationCard
                          event={event}
                          key={`${event.id}:${String(event.payload.confirmation_id)}`}
                          onDecided={() =>
                            void selectSession(active.session_id)
                          }
                          projectId={projectId}
                          sessionId={active.session_id}
                        />
                      ))
                  : null}
                {sending && !streamingContent ? <TypingIndicator /> : null}
              </div>
            )}
          </div>

          <div className="shrink-0 border-t border-[var(--hairline)] p-4">
            <div className="mx-auto flex max-w-3xl gap-2">
              <Input
                aria-label="对话输入"
                className="flex-1"
                disabled={sending}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void handleSend();
                  }
                }}
                placeholder="向超级测试 Agent 描述目标…"
                value={input}
              />
              <Button
                aria-label="发送"
                disabled={sending || !input.trim()}
                loading={sending}
                onClick={() => void handleSend()}
                variant="primary"
              >
                <Send className="size-4" />
              </Button>
            </div>
            {error ? (
              <p
                className="mx-auto mt-2 max-w-3xl text-sm text-[var(--danger)]"
                role="alert"
              >
                {error}
              </p>
            ) : null}
          </div>
        </main>

        <div className="max-[1100px]:hidden">
          <ContextPanel
            artifacts={artifacts}
            events={events}
            projectId={projectId}
          />
        </div>
      </div>
    </div>
  );
}

function WorkspaceTabs({
  value,
  onChange,
}: {
  value: "super" | "target";
  onChange: (value: "super" | "target") => void;
}) {
  return (
    <div className="flex h-12 items-end gap-1 border-b border-[var(--hairline)] px-4">
      <Button
        onClick={() => onChange("super")}
        variant={value === "super" ? "primary" : "ghost"}
      >
        超级 Agent
      </Button>
      <Button
        onClick={() => onChange("target")}
        variant={value === "target" ? "primary" : "ghost"}
      >
        被测 Agent 对话
      </Button>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const user = message.role === "user";
  return (
    <div className={`flex gap-3 ${user ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex size-8 shrink-0 items-center justify-center rounded-full ${user ? "bg-[var(--primary)] text-white" : "bg-[var(--canvas-soft)]"}`}
      >
        {user ? <User className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div
        className={`max-w-[82%] whitespace-pre-wrap rounded-lg px-4 py-2.5 text-sm ${user ? "bg-[var(--primary)] text-white" : "bg-[var(--surface)] text-[var(--ink)] shadow-sm"}`}
      >
        {message.content}
      </div>
    </div>
  );
}
