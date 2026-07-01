"use client";

import { ArrowDown, ChevronsRight, CornerDownLeft, StopCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ChatEmptyState,
  MessageBubble as UIMessageBubble,
  ReasoningBlock,
  ToolCallCard,
  TypingIndicator,
} from "@/components/uiverse";
import type { TaskState } from "@/components/uiverse";

import {
  createSession,
  decideConfirmationsBatch,
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
import { ConfirmationCard } from "./confirmation-card";
import { ContextPanel } from "./context-panel";
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
  const [loadingSession, setLoadingSession] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedInput, setLastFailedInput] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem("chat-sidebar-open") !== "false";
  });
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sessionRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const sseCloseRef = useRef<(() => void) | null>(null);
  const pinnedBottomRef = useRef(true);
  const acceptDeltasRef = useRef(true);
  const [isPinned, setIsPinned] = useState(true);
  const activeSessionId = active?.session_id ?? null;

  // Load sessions on mount
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

  // SSE subscription
  useEffect(() => {
    if (!activeSessionId) return;
    sessionRef.current = activeSessionId;
    sseCloseRef.current?.();
    sseCloseRef.current = subscribeToSession(projectId, activeSessionId, (event) => {
      if (sessionRef.current !== activeSessionId) return;
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
      if (event.type === "message.started") {
        acceptDeltasRef.current = true;
        setStreamingContent("");
      }
      if (event.type === "message.delta" && acceptDeltasRef.current) {
        setStreamingContent(
          (current) => current + String(event.payload.content ?? ""),
        );
      }
      // message.completed is intentionally NOT clearing streamingContent —
      // applySession handles the cleanup when the POST response arrives,
      // preventing a flash between the streaming bubble disappearing
      // and the completed message bubble appearing.
    });
    return () => sseCloseRef.current?.();
  }, [activeSessionId, projectId]);

  // Auto-focus input on initial load only (not after every send)
  useEffect(() => {
    if (!loadingHistory) {
      inputRef.current?.focus();
    }
  }, [loadingHistory]);

  // Smooth auto-scroll — only when user is near bottom
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (pinnedBottomRef.current) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages, events, sending]);

  // Track manual scrolling to unpin auto-scroll
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const threshold = 80;
    const atBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    pinnedBottomRef.current = atBottom;
    setIsPinned(atBottom);
  }, []);

  function applySession(session: ChatResponse) {
    acceptDeltasRef.current = false;
    setActive(session);
    setMessages(session.messages);
    setArtifacts(session.artifacts);
    setStreamingContent("");
    setEvents([]);
    window.history.replaceState(
      {},
      "",
      `${window.location.pathname}?session=${session.session_id}`,
    );
  }

  async function selectSession(sessionId: string) {
    setError(null);
    setEvents([]);
    setLoadingSession(true);
    try {
      applySession(await getSession(projectId, sessionId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "会话加载失败");
    } finally {
      setLoadingSession(false);
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
      const remaining = sessions.filter(
        (item) => item.session_id !== sessionId,
      );
      setSessions(remaining);
      if (activeSessionId === sessionId) {
        if (remaining.length > 0) {
          // Auto-select the most recent remaining session
          await selectSession(remaining[0].session_id);
        } else {
          setActive(null);
          setMessages([]);
          setArtifacts([]);
          setEvents([]);
          window.history.replaceState({}, "", window.location.pathname);
        }
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "删除会话失败");
    }
  }

  function stopGenerating() {
    abortRef.current?.abort();
    sseCloseRef.current?.();
    sseCloseRef.current = null;
    setSending(false);
    setStreamingContent("");
  }

  async function handleSend() {
    const content = input.trim();
    if (!content || sending) return;
    setInput("");
    setLastFailedInput(null);
    setSending(true);
    setError(null);
    pinnedBottomRef.current = true;
    abortRef.current = new AbortController();

    // Optimistically show the user message immediately
    const pendingUserMessage: ChatMessage = {
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((current) => [...current, pendingUserMessage]);

    try {
      const session: ChatResponse =
        active ?? (await createSession(projectId));
      if (!active) {
        // Update session state manually — applySession would wipe the
        // optimistic user message we just added above.
        setActive(session);
        setArtifacts(session.artifacts);
        setSessions((current) => [session, ...current]);
        window.history.replaceState(
          {},
          "",
          `${window.location.pathname}?session=${session.session_id}`,
        );
      }
      const response = await sendChatMessage(
        projectId,
        session.session_id,
        content,
        abortRef.current.signal,
      );
      applySession(response);
      setSessions((current) => [
        response,
        ...current.filter((item) => item.session_id !== response.session_id),
      ]);
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      // Remove the optimistic message on failure
      setMessages((current) =>
        current.filter((msg) => msg.timestamp !== pendingUserMessage.timestamp),
      );
      setInput(content);
      setLastFailedInput(content);
      setError(
        reason instanceof TestAgentApiError || reason instanceof Error
          ? reason.message
          : "对话失败，请重试。",
      );
    } finally {
      setSending(false);
      abortRef.current = null;
    }
  }

  const handleToggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => {
      const next = !prev;
      localStorage.setItem("chat-sidebar-open", String(next));
      return next;
    });
  }, []);

  if (workspace === "target") {
    return (
      <div className="flex h-full flex-col overflow-hidden">
        <WorkspaceTabs value={workspace} onChange={setWorkspace} />
        <TargetChatScreen projectId={projectId} />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <WorkspaceTabs value={workspace} onChange={setWorkspace} />

      <div className="relative min-h-0 flex-1 overflow-hidden">
        {/* Floating sidebar overlay */}
        <aside
          className={`absolute bottom-0 left-0 top-0 z-20 w-64 transition-transform duration-300 ease-in-out ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <SessionList
            activeId={active?.session_id ?? null}
            items={sessions}
            loading={loadingHistory}
            onCreate={() => void newSession()}
            onDelete={(id) => void handleDelete(id)}
            onSelect={(id) => void selectSession(id)}
            onToggleCollapse={handleToggleSidebar}
          />
        </aside>

        {/* Backdrop when sidebar is open on narrow screens */}
        {sidebarOpen ? (
          <div
            aria-hidden="true"
            className="absolute inset-0 z-10 bg-black/20 transition-opacity max-[1100px]:block hidden"
            onClick={handleToggleSidebar}
          />
        ) : null}

        {/* Main + context panel — shifts right when sidebar opens */}
        <div
          className={`grid h-full grid-cols-[minmax(0,1fr)_19rem] max-[1100px]:grid-cols-1 overflow-hidden transition-[margin] duration-300 ease-in-out ${
            sidebarOpen ? "ml-64" : "ml-0"
          }`}
        >

        <main className="relative flex min-h-0 min-w-0 flex-col bg-[var(--canvas)]">
          {/* Header always visible with sidebar toggle */}
          <header className="flex shrink-0 items-center justify-between border-b border-[var(--hairline)] bg-[var(--canvas)] px-4 py-2.5">
            <button
              aria-label="切换侧边栏"
              className="rounded-lg p-1.5 text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
              onClick={handleToggleSidebar}
              type="button"
            >
              <ChevronsRight className={`size-4 transition-transform ${sidebarOpen ? "rotate-180" : ""}`} />
            </button>
            <span className="text-sm font-medium text-[var(--ink)] truncate mx-3">
              {active?.title ?? "超级测试 Agent"}
            </span>
            <div className="w-8" />
          </header>

          <div
            className="chat-scroll min-h-0 flex-1 overflow-y-auto px-5 py-4"
            onScroll={handleScroll}
            ref={scrollRef}
          >
            {/* Session loading indicator */}
            {loadingSession ? (
              <div className="mx-auto max-w-3xl">
                <div className="mb-2 h-0.5 w-full overflow-hidden rounded-full bg-[var(--canvas-soft)]">
                  <div className="h-full w-1/3 animate-[loading-bar_1.5s_ease-in-out_infinite] rounded-full bg-[var(--primary)]" />
                </div>
              </div>
            ) : null}
            {messages.length === 0 && !sending && !streamingContent ? (
              <ChatEmptyState
                description="告诉我你想测试什么，我会帮你编排完整的测试流程"
                onSuggestionClick={setInput}
                suggestions={[
                  "为登录 API 生成回归测试用例并执行",
                  "对比 Agent v2.3 和 v2.2 的评分差异",
                  "执行安全红队测试并检查发布门禁",
                  "帮我注册一个 HTTP Agent 并创建测试计划",
                ]}
                title="有什么我可以帮你的？"
              />
            ) : (
              <Timeline
                active={active}
                events={events}
                messages={messages}
                onSessionReload={(id) => void selectSession(id)}
                projectId={projectId}
                sending={sending}
                streamingContent={streamingContent}
              />
            )}
          </div>

          {/* Scroll-to-bottom floating button — any time user scrolls up */}
          {!isPinned ? (
            <div className="flex justify-center">
              <button
                aria-label="滚动到底部"
                className="absolute bottom-20 z-10 rounded-full border border-[var(--hairline)] bg-[var(--surface)] p-2 text-[var(--muted)] shadow-md transition-all hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)] hover:shadow-lg"
                onClick={() => {
                  const el = scrollRef.current;
                  if (el) {
                    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
                    pinnedBottomRef.current = true;
                    setIsPinned(true);
                  }
                }}
                type="button"
              >
                <ArrowDown className="size-4" />
              </button>
            </div>
          ) : null}

          {/* Error banner — fixed above input bar */}
          {error ? (
            <div
              className="shrink-0 border-t border-[var(--danger)]/30 bg-[var(--danger-subtle)]/20 px-4 py-2.5"
              role="alert"
            >
              <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-[var(--danger)]">{error}</p>
                  {lastFailedInput ? (
                    <p className="mt-0.5 truncate text-[0.65rem] text-[var(--muted)]">
                      消息: {lastFailedInput.slice(0, 60)}
                      {lastFailedInput.length > 60 ? "…" : ""}
                    </p>
                  ) : null}
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  {lastFailedInput ? (
                    <button
                      className="rounded px-2 py-0.5 text-xs text-[var(--primary)] transition-colors hover:bg-[var(--primary)]/10"
                      onClick={() => {
                        if (lastFailedInput) {
                          setInput(lastFailedInput);
                          void handleSend();
                        }
                      }}
                      type="button"
                    >
                      重试
                    </button>
                  ) : null}
                  <button
                    className="rounded px-2 py-0.5 text-xs text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
                    onClick={() => {
                      setError(null);
                      setLastFailedInput(null);
                    }}
                    type="button"
                  >
                    关闭
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          <div className="shrink-0 border-t border-[var(--hairline)] px-4 py-3">
            <div className="mx-auto flex max-w-3xl gap-2">
              <div className="relative flex-1">
                <textarea
                  aria-label="对话输入"
                  className="w-full resize-none rounded-2xl border border-[var(--hairline)] bg-[var(--canvas-soft)] px-4 py-3 pr-10 text-[0.9375rem] leading-6 text-[var(--ink)] placeholder-[var(--muted)] transition-shadow focus:border-[var(--hairline-strong)] focus:shadow-md focus:outline-none disabled:opacity-50"
                  disabled={sending}
                  onChange={(event) => {
                    setInput(event.target.value);
                    // Auto-resize
                    const el = event.target;
                    el.style.height = "auto";
                    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      void handleSend();
                    }
                  }}
                  placeholder="向超级测试 Agent 描述目标…"
                  ref={inputRef}
                  rows={1}
                  value={input}
                />
                {sending ? (
                  <button
                    aria-label="停止生成"
                    className="absolute bottom-2 right-2 rounded-lg p-1.5 text-[var(--muted)] transition-colors hover:bg-[var(--danger-subtle)] hover:text-[var(--danger)]"
                    onClick={stopGenerating}
                    type="button"
                  >
                    <StopCircle className="size-5" />
                  </button>
                ) : (
                  <button
                    aria-label="发送"
                    className={`absolute bottom-2 right-2 rounded-lg p-1.5 transition-all ${
                      input.trim()
                        ? "bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]"
                        : "cursor-default text-[var(--muted)]"
                    }`}
                    disabled={!input.trim()}
                    onClick={() => void handleSend()}
                    type="button"
                  >
                    <CornerDownLeft className="size-5" />
                  </button>
                )}
              </div>
            </div>
            <p className="mx-auto mt-2 max-w-3xl text-center text-[0.65rem] text-[var(--muted)]">
              超级测试 Agent 可能产生不准确信息，请验证关键结果。
            </p>
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
    </div>
  );
}

/* ───── Timeline ───── */

type TimelineProps = {
  active: ChatResponse | null;
  events: AgentEvent[];
  messages: ChatMessage[];
  onSessionReload: (sessionId: string) => void;
  projectId: string;
  sending: boolean;
  streamingContent: string;
};

function Timeline({
  active,
  events,
  messages,
  onSessionReload,
  projectId,
  sending,
  streamingContent,
}: TimelineProps) {
  // Tool events grouped by task_id
  const taskStates: TaskState[] = (() => {
    const groups = new Map<
      string,
      { delegated: AgentEvent | null; latest: AgentEvent }
    >();
    const order: string[] = [];
    for (const event of events) {
      if (
        !["agent.delegated", "agent.progress", "agent.completed", "agent.failed"].includes(event.type)
      ) continue;
      const tid = String(event.payload.task_id ?? "");
      if (!tid) continue;
      if (!groups.has(tid)) order.push(tid);
      const existing = groups.get(tid);
      if (!existing) {
        groups.set(tid, { delegated: null, latest: event });
      } else {
        existing.latest = event;
      }
      if (event.type === "agent.delegated") {
        groups.get(tid)!.delegated = event;
      }
    }
    return order.map((tid) => {
      const group = groups.get(tid)!;
      const inputSummary = group.delegated
        ? String(group.delegated.payload.input_summary ?? "")
        : "";
      const childAgent = group.delegated
        ? String(group.delegated.payload.child_agent ?? "")
        : String(group.latest.payload.child_agent ?? "");
      const capability = group.delegated
        ? String(group.delegated.payload.capability ?? "")
        : String(group.latest.payload.capability ?? "");
      const statusMap: Record<string, TaskState["status"]> = {
        "agent.delegated": "delegated",
        "agent.progress": "running",
        "agent.completed": "completed",
        "agent.failed": "failed",
      };
      const status = statusMap[group.latest.type] ?? "delegated";
      return {
        taskId: tid,
        childAgent,
        capability,
        inputSummary,
        status,
        output:
          group.latest.type === "agent.completed"
            ? (group.latest.payload.output as Record<string, unknown> | null) ?? null
            : null,
        errorDetail:
          group.latest.type === "agent.failed"
            ? String(group.latest.payload.detail ?? null)
            : null,
      };
    });
  })();

  const reasoningEvents = events.filter((e) => e.type === "agent.reasoning");
  const errorEvents = events.filter(
    (e) => e.type === "error" && !e.payload.task_id,
  );
  const pendingConfs = events.filter(
    (e) => e.type === "tool.confirmation_required",
  );

  // Build a map: step number → reasoning event
  const reasoningByStep = new Map<number, AgentEvent>();
  for (const evt of reasoningEvents) {
    const step = Number(evt.payload.step ?? 0);
    if (step > 0) reasoningByStep.set(step, evt);
  }

  const batchConfirm = async (approved: boolean) => {
    const ids = pendingConfs.map((e) =>
      String(e.payload.confirmation_id),
    );
    if (ids.length === 0 || !active) return;
    await decideConfirmationsBatch(
      projectId,
      active.session_id,
      ids,
      approved,
    );
  };

  /* ───── Time helpers for message grouping ───── */
  function getTimeGapMinutes(a: string, b: string): number {
    const ta = new Date(a).getTime();
    const tb = new Date(b).getTime();
    if (Number.isNaN(ta) || Number.isNaN(tb)) return 0;
    return Math.abs(tb - ta) / 60_000;
  }

  function formatRelativeDate(iso: string): string {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "";
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60_000);
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

  return (
    <div className="mx-auto max-w-3xl">
      {messages.map((message, index) => {
        const showDivider =
          index > 0 &&
          message.timestamp !== "streaming" &&
          messages[index - 1].timestamp !== "streaming" &&
          getTimeGapMinutes(
            messages[index - 1].timestamp,
            message.timestamp,
          ) > 5;
        return (
          <div key={`${message.timestamp}:${index}`}>
            {showDivider ? (
              <div className="flex items-center gap-3 py-2">
                <div className="h-px flex-1 bg-[var(--hairline)]" />
                <span className="shrink-0 text-[0.6rem] text-[var(--muted)]">
                  {formatRelativeDate(message.timestamp)}
                </span>
                <div className="h-px flex-1 bg-[var(--hairline)]" />
              </div>
            ) : null}
            <div className="timeline-item mb-8 animate-fadeIn last:mb-0">
              <ChatMessageBubble
                message={message}
              />
            </div>
          </div>
        );
      })}

      {/* Streaming message */}
      {streamingContent ? (
        <div className="timeline-item mb-8 animate-fadeIn">
          <ChatMessageBubble
            isStreaming
            message={{
              role: "assistant",
              content: streamingContent,
              timestamp: "streaming",
            }}
          />
        </div>
      ) : null}

      {/* Tool cards interleaved with reasoning (by insertion order) */}
      {taskStates.length > 0 ? (
        <div className="mt-3 space-y-1">
          {taskStates.map((task, i) => {
            const step = i + 1;
            const reasoning = reasoningByStep.get(step);
            return (
              <div key={`task:${task.taskId}`}>
                {reasoning ? (
                  <div className="timeline-item animate-fadeIn mb-1">
                    <ReasoningBlock
                      capability={String(reasoning.payload.capability ?? "")}
                      content={String(reasoning.payload.content ?? "")}
                      step={Number(reasoning.payload.step ?? step)}
                      total={Number(reasoning.payload.total ?? taskStates.length)}
                    />
                  </div>
                ) : null}
                <div className="timeline-item animate-slideIn">
                  <ToolCallCard task={task} />
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

      {/* Remaining reasoning events not matched to a task */}
      {reasoningEvents
        .filter((evt) => !reasoningByStep.has(Number(evt.payload.step ?? 0)))
        .map((evt) => (
          <div
            className="timeline-item animate-fadeIn"
            key={`reasoning:${evt.id}`}
          >
            <ReasoningBlock
              capability={String(evt.payload.capability ?? "")}
              content={String(evt.payload.content ?? "")}
              step={Number(evt.payload.step ?? 0)}
              total={Number(evt.payload.total ?? 0)}
            />
          </div>
        ))}

      {/* Error events */}
      {errorEvents.map((event) => (
        <div
          className="timeline-item animate-fadeIn"
          key={`error:${event.id}`}
        >
          <div className="rounded-[var(--radius-md)] border border-[var(--danger)]/30 bg-[var(--danger-subtle)]/20 px-3 py-2.5">
            <p className="text-xs text-[var(--danger)]">
              {String(event.payload.detail ?? "执行出错")}
            </p>
          </div>
        </div>
      ))}

      {/* Confirmation cards */}
      {active && pendingConfs.length > 0 ? (
        <div className="mt-3 space-y-3">
          {pendingConfs.length > 1 ? (
            <div className="timeline-item animate-fadeIn rounded-[var(--radius-lg)] border border-[var(--warning)]/30 bg-[var(--warning-subtle)]/20 p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[var(--warning)]">
                  {pendingConfs.length} 项待确认操作
                </span>
                <div className="flex gap-1.5">
                  <Button
                    className="h-7 text-xs"
                    onClick={() => void batchConfirm(false)}
                    variant="secondary"
                  >
                    全部拒绝
                  </Button>
                  <Button
                    className="h-7 text-xs"
                    onClick={() => void batchConfirm(true)}
                    variant="primary"
                  >
                    全部批准
                  </Button>
                </div>
              </div>
            </div>
          ) : null}
          {pendingConfs.map((event) => (
            <div
              className="timeline-item animate-fadeIn"
              key={`conf:${event.id}:${String(event.payload.confirmation_id)}`}
            >
              <ConfirmationCard
                event={event}
                onDecided={() => {
                  if (active) onSessionReload(active.session_id);
                }}
                projectId={projectId}
                sessionId={active.session_id}
              />
            </div>
          ))}
        </div>
      ) : null}

      {sending && !streamingContent ? (
        <div className="timeline-item animate-fadeIn">
          <TypingIndicator />
        </div>
      ) : null}
    </div>
  );
}

/* ───── Workspace Tabs ───── */

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

/* ───── Message Bubble (thin wrapper) ───── */

function ChatMessageBubble({
  message,
  isStreaming,
}: {
  message: ChatMessage;
  isStreaming?: boolean;
}) {
  return (
    <UIMessageBubble
      animate
      content={message.content}
      isStreaming={isStreaming}
      role={message.role}
      timestamp={message.timestamp}
    />
  );
}
