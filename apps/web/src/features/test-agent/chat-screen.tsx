"use client";

import { Send, Sparkles, Square } from "lucide-react";
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
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedInput, setLastFailedInput] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sessionRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const sseCloseRef = useRef<(() => void) | null>(null);
  const pinnedBottomRef = useRef(true);
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
      if (event.type === "message.started") setStreamingContent("");
      if (event.type === "message.delta") {
        setStreamingContent(
          (current) => current + String(event.payload.content ?? ""),
        );
      }
      if (event.type === "message.completed") setStreamingContent("");
    });
    return () => sseCloseRef.current?.();
  }, [activeSessionId, projectId]);

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
    pinnedBottomRef.current =
      el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
  }, []);

  function applySession(session: ChatResponse) {
    setActive(session);
    setMessages(session.messages);
    setArtifacts(session.artifacts);
    window.history.replaceState(
      {},
      "",
      `${window.location.pathname}?session=${session.session_id}`,
    );
  }

  async function selectSession(sessionId: string) {
    setError(null);
    setEvents([]);
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
    try {
      const session = active ?? (await newSession());
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
            className="chat-scroll min-h-0 flex-1 overflow-y-auto px-5 py-4"
            onScroll={handleScroll}
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
              <Timeline
                active={active}
                error={error}
                events={events}
                lastFailedInput={lastFailedInput}
                messages={messages}
                onErrorClear={() => {
                  setError(null);
                  setLastFailedInput(null);
                }}
                onRetry={() => {
                  if (lastFailedInput) {
                    setInput(lastFailedInput);
                    void handleSend();
                  }
                }}
                onSessionReload={(id) => void selectSession(id)}
                projectId={projectId}
                sending={sending}
                streamingContent={streamingContent}
              />
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
              {sending ? (
                <Button
                  aria-label="停止生成"
                  onClick={stopGenerating}
                  variant="secondary"
                >
                  <Square className="size-4" />
                </Button>
              ) : (
                <Button
                  aria-label="发送"
                  disabled={!input.trim()}
                  onClick={() => void handleSend()}
                  variant="primary"
                >
                  <Send className="size-4" />
                </Button>
              )}
            </div>
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

/* ───── Timeline ───── */

type TimelineProps = {
  active: ChatResponse | null;
  error: string | null;
  events: AgentEvent[];
  lastFailedInput: string | null;
  messages: ChatMessage[];
  onErrorClear: () => void;
  onRetry: () => void;
  onSessionReload: (sessionId: string) => void;
  projectId: string;
  sending: boolean;
  streamingContent: string;
};

function Timeline({
  active,
  error,
  events,
  lastFailedInput,
  messages,
  onErrorClear,
  onRetry,
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

  return (
    <div className="mx-auto max-w-3xl space-y-1">
      {messages.map((message, index) => (
        <div
          className="timeline-item animate-fadeIn"
          key={`${message.timestamp}:${index}`}
        >
          <ChatMessageBubble
            message={message}
            key={`${message.timestamp}:${index}`}
          />
        </div>
      ))}

      {/* Streaming message */}
      {streamingContent ? (
        <div className="timeline-item animate-fadeIn">
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

      {/* Global error banner */}
      {error ? (
        <div
          className="timeline-item animate-fadeIn mt-3 rounded-[var(--radius-md)] border border-[var(--danger)]/30 bg-[var(--danger-subtle)]/20 px-3 py-2.5"
          role="alert"
        >
          <div className="flex items-center justify-between">
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
                  className="rounded px-2 py-0.5 text-xs text-[var(--primary)] hover:bg-[var(--primary)]/10 transition-colors"
                  onClick={onRetry}
                  type="button"
                >
                  重试
                </button>
              ) : null}
              <button
                className="rounded px-2 py-0.5 text-xs text-[var(--muted)] hover:text-[var(--ink)] transition-colors"
                onClick={onErrorClear}
                type="button"
              >
                关闭
              </button>
            </div>
          </div>
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
