"use client";

import {
  ArrowDown,
  ChevronsRight,
  CornerDownLeft,
  PanelRight,
  StopCircle,
  X,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type MouseEvent,
} from "react";

import { Button } from "@/components/ui/button";
import {
  ChatEmptyState,
  MessageBubble as UIMessageBubble,
  ReasoningBlock,
  ToolCallCard,
  TypingIndicator,
} from "@/components/uiverse";
import type { TaskState } from "@/components/uiverse";

import {
  cancelGeneration,
  createSession,
  decideConfirmationsBatch,
  deleteSession,
  getSession,
  listSessions,
  regenerateMessage,
  sendChatMessage,
  subscribeToSession,
  TestAgentApiError,
} from "./api";
import type { AgentEvent, ChatMessage, ChatResponse } from "./api";
import { createGenerationStreamController } from "./chat-effects";
import { useChatReducer } from "./chat-reducer";
import {
  buildTaskStates,
  formatRelativeDate,
  getTimeGapMinutes,
} from "./chat-workspace-model";
import { ConfirmationCard } from "./confirmation-card";
import { ConversationTimeline } from "./chat-timeline";
import { ContextPanel } from "./context-panel";
import { SessionList } from "./session-list";
import { TargetChatScreen } from "./target-chat-screen";

// ── 主组件 ───────────────────────────────────────────────────────

export function ChatWorkspace({ projectId }: { projectId: string }) {
  const { state, dispatch, applySession, addSseEvent } = useChatReducer();

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sessionRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const pinnedBottomRef = useRef(true);
  const acceptDeltasRef = useRef(true);
  const streamingContentRef = useRef("");
  const resizingRef = useRef(false);
  const [contextOpen, setContextOpen] = useState(false);

  const activeSessionId = state.activeSession?.session_id ?? null;
  const streamController = useMemo(
    () =>
      createGenerationStreamController<AgentEvent>(
        (sessionId, onEvent, onError, cursor) =>
          subscribeToSession(projectId, sessionId, onEvent, onError, cursor),
        { cursorFor: (event) => event.id },
      ),
    [projectId],
  );

  useEffect(() => {
    streamingContentRef.current = state.streamingContent;
  }, [state.streamingContent]);

  // ── Mount: load sessions ──
  useEffect(() => {
    let alive = true;
    const requested = new URLSearchParams(window.location.search).get(
      "session",
    );
    listSessions(projectId)
      .then(async (response) => {
        if (!alive) return;
        dispatch({ type: "SET_SESSIONS", sessions: response.items });
        if (requested) {
          const session = await getSession(projectId, requested);
          if (alive) applySession(session);
        }
      })
      .catch((reason: unknown) => {
        if (alive) {
          dispatch({
            type: "SET_ERROR",
            error:
              reason instanceof Error ? reason.message : "会话历史加载失败",
          });
        }
      })
      .finally(() => {
        if (alive) dispatch({ type: "SET_LOADING_HISTORY", value: false });
      });
    return () => {
      alive = false;
    };
  }, [applySession, dispatch, projectId]);

  // ── SSE subscription ──
  useEffect(() => {
    if (!activeSessionId) return;
    sessionRef.current = activeSessionId;
    return streamController.connect(
      activeSessionId,
      (event) => {
        if (sessionRef.current !== activeSessionId) return;
        // Honour acceptDeltas gate so stopGenerating can suppress streaming without closing SSE
        if (
          !acceptDeltasRef.current &&
          (event.type === "message.delta" ||
            event.type === "agent.reasoning_delta")
        )
          return;

        if (event.type === "stream.ready") {
          dispatch({ type: "SET_CONNECTION", value: "ready" });
          return;
        }
        addSseEvent(event);
      },
      () => dispatch({ type: "SET_CONNECTION", value: "reconnecting" }),
      state.eventCursor,
    );
  }, [
    activeSessionId,
    addSseEvent,
    dispatch,
    state.eventCursor,
    streamController,
  ]);

  useEffect(() => () => streamController.disconnect(), [streamController]);

  // ── Auto-focus ──
  useEffect(() => {
    if (!state.loadingHistory && !state.sending) inputRef.current?.focus();
  }, [state.loadingHistory, state.sending]);

  // ── Smooth auto-scroll ──
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (pinnedBottomRef.current) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [state.messages, state.events, state.sending, state.streamingContent]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    pinnedBottomRef.current = atBottom;
    dispatch({ type: "SET_PINNED", value: atBottom });
  }, [dispatch]);

  // ── Session actions ──
  const selectSession = useCallback(
    async (sessionId: string) => {
      dispatch({ type: "SET_ERROR", error: null });
      dispatch({ type: "SET_LOADING_SESSION", value: true });
      dispatch({ type: "CLEAR_EVENTS" });
      try {
        applySession(await getSession(projectId, sessionId));
      } catch (reason) {
        dispatch({
          type: "SET_ERROR",
          error: reason instanceof Error ? reason.message : "会话加载失败",
        });
      } finally {
        dispatch({ type: "SET_LOADING_SESSION", value: false });
      }
    },
    [projectId, applySession, dispatch],
  );

  const newSession = useCallback(async () => {
    dispatch({ type: "SET_ERROR", error: null });
    const session = await createSession(projectId);
    applySession(session);
    return session;
  }, [projectId, applySession, dispatch]);

  const handleDelete = useCallback(
    async (sessionId: string) => {
      try {
        const response = await deleteSession(projectId, sessionId);
        if (!response.ok) throw new Error("删除失败");
        const remaining = state.sessions.filter(
          (i) => i.session_id !== sessionId,
        );
        dispatch({ type: "SET_SESSIONS", sessions: remaining });
        if (activeSessionId === sessionId) {
          if (remaining.length > 0) {
            await selectSession(remaining[0].session_id);
          } else {
            dispatch({ type: "CLEAR_SESSION" });
            if (typeof window !== "undefined") {
              window.history.replaceState({}, "", window.location.pathname);
            }
          }
        }
      } catch (reason) {
        dispatch({
          type: "SET_ERROR",
          error: reason instanceof Error ? reason.message : "删除会话失败",
        });
      }
    },
    [projectId, state.sessions, activeSessionId, selectSession, dispatch],
  );

  // ── Send / Regenerate ──
  async function stopGenerating() {
    const sessionId = sessionRef.current;
    const generation = state.activeGeneration;
    if (sessionId && generation && generation.status !== "pending") {
      dispatch({
        type: "SET_ACTIVE_GENERATION",
        value: { ...generation, status: "cancelling" },
      });
      try {
        await cancelGeneration(projectId, sessionId, generation.generation_id);
      } catch (reason) {
        dispatch({
          type: "SET_ERROR",
          error: reason instanceof Error ? reason.message : "取消生成失败",
        });
        return;
      }
    }
    abortRef.current?.abort();
    if (generation?.status === "pending") {
      dispatch({ type: "SET_ACTIVE_GENERATION", value: null });
    }
    // Keep SSE alive – just gate deltas with acceptDeltasRef
    acceptDeltasRef.current = false;
    const partial = streamingContentRef.current.trim();
    if (partial) {
      dispatch({
        type: "APPEND_MESSAGE",
        message: {
          role: "assistant",
          content: partial,
          timestamp: new Date().toISOString(),
        },
      });
    }
    dispatch({ type: "SET_SENDING", value: false });
    dispatch({ type: "SET_STREAMING_ACTIVE", value: false });
    dispatch({ type: "CLEAR_STREAMING" });
  }

  async function handleRegenerate(editedMessage?: string) {
    if (!activeSessionId) return;
    dispatch({ type: "SET_SENDING", value: true });
    dispatch({ type: "SET_STREAMING_ACTIVE", value: true });
    dispatch({ type: "SET_ERROR", error: null });
    pinnedBottomRef.current = true;
    acceptDeltasRef.current = true;
    abortRef.current = new AbortController();

    dispatch({
      type: "FILTER_EVENTS",
      keepTypes: ["message.started", "message.delta"],
    });
    dispatch({ type: "REMOVE_LAST_ASSISTANT_MESSAGE" });

    if (editedMessage) {
      dispatch({ type: "REPLACE_LAST_USER_MESSAGE", content: editedMessage });
      dispatch({ type: "REMOVE_LAST_ASSISTANT_MESSAGE" });
    }

    try {
      const response = await regenerateMessage(
        projectId,
        activeSessionId,
        editedMessage,
        abortRef.current.signal,
      );
      applySession(response);
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError")
        return;
      dispatch({
        type: "SET_ERROR",
        error:
          reason instanceof TestAgentApiError || reason instanceof Error
            ? reason.message
            : "重新生成失败，请重试。",
      });
    } finally {
      dispatch({ type: "SET_SENDING", value: false });
      abortRef.current = null;
    }
  }

  async function handleSend() {
    const content = state.input.trim();
    if (!content || state.sending) return;
    dispatch({ type: "SET_INPUT", value: "" });
    dispatch({ type: "SET_ERROR", error: null, lastInput: null });
    dispatch({ type: "SET_SENDING", value: true });
    dispatch({ type: "SET_STREAMING_ACTIVE", value: true });
    pinnedBottomRef.current = true;
    acceptDeltasRef.current = true;
    abortRef.current = new AbortController();

    // Ensure SSE is open before POST (may have been closed by stopGenerating or race)
    const ensureSseOpen = (sid: string) =>
      new Promise<void>((resolve, reject) => {
        sessionRef.current = sid;
        let unsubscribe: () => void = () => undefined;
        const timeout = window.setTimeout(() => {
          unsubscribe();
          reject(new Error("实时连接建立超时"));
        }, 5000);
        unsubscribe = streamController.connect(
          sid,
          (event) => {
            if (sessionRef.current !== sid) return;
            if (event.type === "stream.ready") {
              window.clearTimeout(timeout);
              unsubscribe();
              dispatch({ type: "SET_CONNECTION", value: "ready" });
              resolve();
            }
          },
          () => dispatch({ type: "SET_CONNECTION", value: "reconnecting" }),
          state.eventCursor,
        );
      });

    dispatch({
      type: "FILTER_EVENTS",
      keepTypes: ["message.started", "message.delta"],
    });

    const pendingUserMessage: ChatMessage = {
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    dispatch({ type: "APPEND_MESSAGE", message: pendingUserMessage });

    try {
      const session: ChatResponse =
        state.activeSession ?? (await createSession(projectId));
      const generationId = crypto.randomUUID();
      dispatch({
        type: "SET_ACTIVE_GENERATION",
        value: {
          generation_id: generationId,
          status: "pending",
          partial_content: "",
          workflow_id: null,
        },
      });
      await ensureSseOpen(session.session_id);
      if (abortRef.current.signal.aborted) return;
      if (!state.activeSession) {
        // Activate session metadata without wiping optimistic user message
        applySession(session);
        // Restore optimistic user message that applySession wiped
        dispatch({ type: "APPEND_MESSAGE", message: pendingUserMessage });
      }
      const response = await sendChatMessage(
        projectId,
        session.session_id,
        content,
        generationId,
        abortRef.current.signal,
      );
      applySession(response);
      // Gate residual SSE deltas that arrive after session is fully loaded
      acceptDeltasRef.current = false;
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError")
        return;
      dispatch({ type: "REMOVE_LAST_USER_MESSAGE" });
      dispatch({ type: "SET_INPUT", value: content });
      dispatch({
        type: "SET_ERROR",
        error:
          reason instanceof TestAgentApiError || reason instanceof Error
            ? reason.message
            : "对话失败，请重试。",
        lastInput: content,
      });
    } finally {
      dispatch({ type: "SET_SENDING", value: false });
      abortRef.current = null;
    }
  }

  // ── Sidebar ──
  const handleToggleSidebar = useCallback(() => {
    dispatch({ type: "TOGGLE_SIDEBAR" });
  }, [dispatch]);

  const handleResizeStart = useCallback(
    (e: MouseEvent) => {
      e.preventDefault();
      resizingRef.current = true;
      const startX = e.clientX;
      const startWidth = state.sidebarWidth;

      const onMove = (ev: globalThis.MouseEvent) => {
        if (!resizingRef.current) return;
        dispatch({
          type: "SET_SIDEBAR_WIDTH",
          width: Math.max(
            200,
            Math.min(480, startWidth + (ev.clientX - startX)),
          ),
        });
      };
      const onUp = () => {
        resizingRef.current = false;
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      };
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    },
    [state.sidebarWidth, dispatch],
  );

  // ── Keyboard shortcuts ──
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter: send immediately
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void handleSend();
      return;
    }
    // Enter (no shift): send
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
      return;
    }
    // Ctrl+K: new session
    if (e.key === "k" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void newSession();
    }
  };

  // ── Target Chat workspace ──
  if (state.workspace === "target") {
    return (
      <div className="flex h-full flex-col overflow-hidden">
        <WorkspaceTabs
          value={state.workspace}
          onChange={(v) => dispatch({ type: "SET_WORKSPACE", value: v })}
        />
        <TargetChatScreen projectId={projectId} />
      </div>
    );
  }

  // ── Build task states from events ──
  const taskStates = buildTaskStates(state.events);
  const reasoningEvents = state.events.filter(
    (e) => e.type === "agent.reasoning",
  );
  const reasoningByStep = new Map<number, AgentEvent>();
  for (const evt of reasoningEvents) {
    const step = Number(evt.payload.step ?? 0);
    if (step > 0) reasoningByStep.set(step, evt);
  }
  const errorEvents = state.events.filter(
    (e) => e.type === "error" && !e.payload.task_id,
  );
  const pendingConfs = state.events.filter(
    (e) => e.type === "tool.confirmation_required",
  );

  const batchConfirm = async (approved: boolean) => {
    const ids = pendingConfs.map((e) => String(e.payload.confirmation_id));
    if (ids.length === 0 || !state.activeSession) return;
    try {
      await decideConfirmationsBatch(
        projectId,
        state.activeSession.session_id,
        ids,
        approved,
        String(pendingConfs[0]?.payload.generation_id ?? "") || undefined,
      );
    } finally {
      void selectSession(state.activeSession.session_id);
    }
  };

  const lastAssistantIndex = (() => {
    for (let i = state.messages.length - 1; i >= 0; i--) {
      if (state.messages[i].role === "assistant") return i;
    }
    return -1;
  })();

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <WorkspaceTabs
        value={state.workspace}
        onChange={(v) => dispatch({ type: "SET_WORKSPACE", value: v })}
      />

      <div className="relative min-h-0 flex-1 overflow-hidden">
        {/* ── Sidebar ── */}
        <aside
          className={`absolute bottom-0 left-0 top-0 z-30 max-[760px]:w-[min(86vw,20rem)] transition-transform duration-200 ease-out ${
            state.sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
          style={{ width: state.sidebarWidth }}
        >
          <SessionList
            activeId={state.activeSession?.session_id ?? null}
            items={state.sessions}
            loading={state.loadingHistory}
            onCreate={() => void newSession()}
            onDelete={(id) => void handleDelete(id)}
            onSelect={(id) => void selectSession(id)}
          />
          {state.sidebarOpen ? (
            <div
              aria-label="拖拽调整侧边栏宽度"
              className="absolute bottom-0 right-0 top-0 z-30 w-1 cursor-col-resize transition-colors hover:bg-[var(--primary)]/30"
              onMouseDown={handleResizeStart}
              role="separator"
            />
          ) : null}
        </aside>

        {state.sidebarOpen ? (
          <div
            aria-hidden="true"
            className="absolute inset-0 z-20 hidden bg-black/20 backdrop-blur-[1px] max-[760px]:block"
            onClick={handleToggleSidebar}
          />
        ) : null}

        {/* ── Main + Context ── */}
        <div
          className="grid h-full grid-cols-[minmax(0,1fr)_18rem] overflow-hidden transition-[margin] duration-200 ease-out max-[1100px]:grid-cols-1 max-[760px]:ml-0 ml-[var(--chat-sidebar-width)]"
          style={
            {
              "--chat-sidebar-width": state.sidebarOpen
                ? `${state.sidebarWidth}px`
                : "0px",
            } as CSSProperties
          }
        >
          <main className="relative flex min-h-0 min-w-0 flex-col bg-[var(--canvas)]">
            {/* Header */}
            <header className="flex h-12 shrink-0 items-center justify-between border-b border-[var(--hairline)] bg-[var(--canvas)] px-3 sm:px-4">
              <button
                aria-label={state.sidebarOpen ? "关闭会话历史" : "打开会话历史"}
                className="flex size-9 items-center justify-center rounded-lg text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
                onClick={handleToggleSidebar}
                type="button"
              >
                <ChevronsRight
                  className={`size-4 transition-transform ${state.sidebarOpen ? "rotate-180" : ""}`}
                />
              </button>
              <span className="mx-3 truncate text-sm font-medium text-[var(--ink)]">
                {state.activeSession?.title ?? "超级测试 Agent"}
              </span>
              <div className="flex items-center gap-1">
                <button
                  aria-label={contextOpen ? "关闭上下文" : "打开上下文"}
                  className="flex size-9 items-center justify-center rounded-lg text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)] min-[1101px]:hidden"
                  onClick={() => setContextOpen((value) => !value)}
                  type="button"
                >
                  <PanelRight className="size-4" />
                </button>
                <button
                  aria-label="新建会话 (Ctrl+K)"
                  className="flex size-9 items-center justify-center rounded-lg text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
                  onClick={() => void newSession()}
                  title="新建会话 (Ctrl+K)"
                  type="button"
                >
                  <span className="text-lg leading-none">+</span>
                </button>
              </div>
            </header>

            {/* Scrollable chat area */}
            <div
              aria-busy={state.sending || state.loadingSession}
              aria-live="polite"
              className="chat-scroll min-h-0 flex-1 overflow-y-auto px-4 pb-8 pt-6 sm:px-6"
              onScroll={handleScroll}
              ref={scrollRef}
              role="log"
            >
              {state.loadingSession ? (
                <LoadingBar />
              ) : state.messages.length === 0 &&
                !state.sending &&
                !state.streamingContent ? (
                <ChatEmptyState
                  description="告诉我你想测试什么，我会帮你编排完整的测试流程"
                  onSuggestionClick={(text) =>
                    dispatch({ type: "SET_INPUT", value: text })
                  }
                  suggestions={[
                    "为登录 API 生成回归测试用例并执行",
                    "对比 Agent v2.3 和 v2.2 的评分差异",
                    "执行安全红队测试并检查发布门禁",
                    "帮我注册一个 HTTP Agent 并创建测试计划",
                  ]}
                  title="有什么我可以帮你的？"
                />
              ) : (
                <MessageTimeline
                  activeSession={state.activeSession}
                  errorEvents={errorEvents}
                  lastAssistantIndex={lastAssistantIndex}
                  messages={state.messages}
                  onEdit={(c) => void handleRegenerate(c)}
                  onRegenerate={() => void handleRegenerate()}
                  onSessionReload={(id) => void selectSession(id)}
                  pendingConfs={pendingConfs}
                  projectId={projectId}
                  reasoningByStep={reasoningByStep}
                  reasoningEvents={reasoningEvents}
                  reasoningStream={state.reasoningStream}
                  sending={state.sending}
                  streamingActive={state.streamingActive}
                  streamingContent={state.streamingContent}
                  taskStates={taskStates}
                  timeline={state.timeline}
                  batchConfirm={batchConfirm}
                />
              )}
            </div>

            {/* Scroll-to-bottom */}
            {!state.isPinned &&
            (state.messages.length > 0 || state.streamingContent) ? (
              <div className="absolute bottom-20 left-1/2 z-10 -translate-x-1/2">
                <button
                  aria-label="滚动到底部"
                  className="rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] p-2 text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
                  onClick={() => {
                    scrollRef.current?.scrollTo({
                      top: scrollRef.current.scrollHeight,
                      behavior: "smooth",
                    });
                    pinnedBottomRef.current = true;
                    dispatch({ type: "SET_PINNED", value: true });
                  }}
                  type="button"
                >
                  <ArrowDown className="size-4" />
                </button>
              </div>
            ) : null}

            {/* Error banner */}
            {state.error ? (
              <div
                aria-live="assertive"
                className="shrink-0 border-t border-[var(--danger)]/30 bg-[var(--danger-subtle)]/20 px-4 py-2.5"
                role="alert"
              >
                <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-[var(--danger)]">
                      {state.error}
                    </p>
                    {state.lastFailedInput ? (
                      <p className="mt-0.5 truncate text-[0.65rem] text-[var(--muted)]">
                        消息: {state.lastFailedInput.slice(0, 60)}
                        {state.lastFailedInput.length > 60 ? "…" : ""}
                      </p>
                    ) : null}
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    {state.lastFailedInput ? (
                      <button
                        className="rounded px-2 py-0.5 text-xs text-[var(--primary)] transition-colors hover:bg-[var(--primary)]/10"
                        onClick={() => {
                          dispatch({
                            type: "SET_INPUT",
                            value: state.lastFailedInput ?? "",
                          });
                          void handleSend();
                        }}
                        type="button"
                      >
                        重试
                      </button>
                    ) : null}
                    <button
                      className="rounded px-2 py-0.5 text-xs text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
                      onClick={() =>
                        dispatch({
                          type: "SET_ERROR",
                          error: null,
                          lastInput: null,
                        })
                      }
                      type="button"
                    >
                      关闭
                    </button>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Composer (input bar) */}
            <div className="shrink-0 bg-[linear-gradient(to_bottom,transparent,var(--canvas)_24%)] px-3 pb-3 pt-6 sm:px-5">
              {state.connectionState === "reconnecting" ||
              state.connectionState === "offline" ? (
                <p
                  className="mx-auto mb-2 max-w-3xl text-xs text-[var(--muted)]"
                  role="status"
                >
                  {state.connectionState === "reconnecting"
                    ? "正在恢复实时连接…"
                    : "实时连接已断开"}
                </p>
              ) : null}
              <div className="mx-auto max-w-3xl">
                <div className="relative rounded-[var(--radius-lg)] border border-[var(--hairline-strong)] bg-[var(--surface)] shadow-[var(--shadow-overlay)] transition-[border-color,box-shadow] focus-within:border-[var(--primary)]">
                  <textarea
                    aria-label="对话输入"
                    className="block max-h-48 min-h-12 w-full resize-none bg-transparent px-4 py-3 pr-12 text-[0.9375rem] leading-6 text-[var(--ink)] placeholder:text-[var(--muted)] focus:outline-none disabled:opacity-50"
                    data-focus-owner="composer"
                    disabled={state.sending}
                    onChange={(e) => {
                      dispatch({ type: "SET_INPUT", value: e.target.value });
                      e.target.style.height = "auto";
                      e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
                    }}
                    onKeyDown={handleKeyDown}
                    placeholder="向超级测试 Agent 描述目标…"
                    ref={inputRef}
                    rows={1}
                    value={state.input}
                  />
                  {state.sending ? (
                    <button
                      aria-label={
                        state.activeGeneration?.status === "cancelling"
                          ? "取消中"
                          : "停止生成"
                      }
                      className="absolute bottom-2 right-2 flex size-8 items-center justify-center rounded-full bg-[var(--ink)] text-[var(--canvas)] transition-colors hover:bg-[var(--danger)] disabled:opacity-50"
                      onClick={() => void stopGenerating()}
                      disabled={state.activeGeneration?.status === "cancelling"}
                      type="button"
                    >
                      <StopCircle className="size-4.5" />
                    </button>
                  ) : (
                    <button
                      aria-label="发送 (Enter)"
                      className={`absolute bottom-2 right-2 flex size-8 items-center justify-center rounded-full transition-colors ${
                        state.input.trim()
                          ? "bg-[var(--ink)] text-[var(--canvas)] hover:opacity-85"
                          : "cursor-default bg-[var(--canvas-soft)] text-[var(--muted)]"
                      }`}
                      disabled={!state.input.trim()}
                      onClick={() => void handleSend()}
                      type="button"
                    >
                      <CornerDownLeft className="size-4.5" />
                    </button>
                  )}
                </div>
                <div className="mt-1.5 px-1 text-[0.65rem] text-[var(--muted)]">
                  <span>Enter 发送 · Shift+Enter 换行</span>
                </div>
              </div>
            </div>
          </main>

          {/* Context panel */}
          <div className="h-full max-[1100px]:hidden">
            <ContextPanel
              artifacts={state.artifacts}
              events={state.events}
              projectId={projectId}
            />
          </div>
        </div>

        {contextOpen ? (
          <div className="absolute inset-0 z-40 hidden max-[1100px]:block">
            <button
              aria-label="关闭上下文"
              className="absolute inset-0 bg-black/20 backdrop-blur-[1px]"
              onClick={() => setContextOpen(false)}
              type="button"
            />
            <aside className="absolute bottom-0 right-0 top-0 w-[min(88vw,18rem)] bg-[var(--surface)] shadow-xl">
              <div className="flex h-12 items-center justify-between border-b border-[var(--hairline)] px-4">
                <span className="text-sm font-medium">上下文</span>
                <button
                  aria-label="关闭上下文面板"
                  className="flex size-9 items-center justify-center rounded-lg text-[var(--muted)] hover:bg-[var(--canvas-soft)]"
                  onClick={() => setContextOpen(false)}
                  type="button"
                >
                  <X className="size-4" />
                </button>
              </div>
              <div className="h-[calc(100%-3rem)]">
                <ContextPanel
                  artifacts={state.artifacts}
                  events={state.events}
                  projectId={projectId}
                />
              </div>
            </aside>
          </div>
        ) : null}
      </div>
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────

type TimelineProps = {
  activeSession: ChatResponse | null;
  errorEvents: AgentEvent[];
  lastAssistantIndex: number;
  messages: ChatMessage[];
  onEdit: (newContent: string) => void;
  onRegenerate: () => void;
  onSessionReload: (sessionId: string) => void;
  pendingConfs: AgentEvent[];
  projectId: string;
  reasoningByStep: Map<number, AgentEvent>;
  reasoningEvents: AgentEvent[];
  reasoningStream: string;
  sending: boolean;
  streamingActive: boolean;
  streamingContent: string;
  taskStates: TaskState[];
  batchConfirm: (approved: boolean) => Promise<void>;
  timeline: import("./api").TimelineItem[];
};

function MessageTimeline({
  activeSession,
  errorEvents,
  lastAssistantIndex,
  messages,
  onEdit,
  onRegenerate,
  onSessionReload,
  pendingConfs,
  projectId,
  reasoningByStep,
  reasoningEvents,
  reasoningStream,
  sending,
  streamingActive,
  streamingContent,
  taskStates,
  batchConfirm,
  timeline,
}: TimelineProps) {
  return (
    <div className="mx-auto max-w-3xl">
      {/* ── Persisted, server-ordered conversation timeline ── */}
      {timeline.length > 0 ? (
        <ConversationTimeline items={timeline} projectId={projectId} />
      ) : null}

      {/* ── Legacy message fallback ── */}
      {timeline.length === 0
        ? messages.map((message, index) => {
            const showDivider =
              index > 0 &&
              getTimeGapMinutes(
                messages[index - 1].timestamp,
                message.timestamp,
              ) > 5;
            const isLastAssistant =
              message.role === "assistant" &&
              index === lastAssistantIndex &&
              !sending &&
              !streamingContent;
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
                    isLastAssistant={isLastAssistant}
                    message={message}
                    onEdit={message.role === "user" ? onEdit : undefined}
                    onRegenerate={isLastAssistant ? onRegenerate : undefined}
                  />
                </div>
              </div>
            );
          })
        : null}

      {/* ── Tool cards + reasoning ── */}
      {timeline.length === 0 &&
        (taskStates.length > 0 || reasoningEvents.length > 0) && (
          <div className="mb-8 space-y-1.5">
            {taskStates.map((task, i) => {
              const step = i + 1;
              const reasoning = reasoningByStep.get(step);
              return (
                <div key={`task:${task.taskId}`}>
                  {reasoning ? (
                    <div className="timeline-item animate-fadeIn mb-1.5">
                      <ReasoningBlock
                        capability={String(reasoning.payload.capability ?? "")}
                        content={String(reasoning.payload.content ?? "")}
                        step={Number(reasoning.payload.step ?? step)}
                        total={Number(
                          reasoning.payload.total ?? taskStates.length,
                        )}
                      />
                    </div>
                  ) : null}
                  <div className="timeline-item animate-slideIn">
                    <ToolCallCard task={task} />
                  </div>
                </div>
              );
            })}
            {reasoningEvents
              .filter(
                (evt) => !reasoningByStep.has(Number(evt.payload.step ?? 0)),
              )
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
          </div>
        )}

      {/* ── Streaming reasoning (Codex-style: inline before reply) ── */}
      {reasoningStream ? (
        <div className="timeline-item mb-2 animate-fadeIn">
          <ReasoningBlock
            content={reasoningStream}
            isStreaming={!streamingContent}
          />
        </div>
      ) : null}

      {/* ── Streaming assistant reply ── */}
      {streamingContent ? (
        <div className="timeline-item mb-8 animate-fadeIn">
          <ChatMessageBubble
            isStreaming={streamingActive}
            message={{
              role: "assistant",
              content: streamingContent,
              timestamp: "",
            }}
          />
        </div>
      ) : sending && !reasoningStream ? (
        <div className="timeline-item mb-8 animate-fadeIn">
          <TypingIndicator />
        </div>
      ) : null}

      {/* ── Error events ── */}
      {errorEvents.map((event) => (
        <div
          className="timeline-item animate-fadeIn mb-4"
          key={`error:${event.id}`}
        >
          <div className="rounded-[var(--radius-md)] border border-[var(--danger)]/30 bg-[var(--danger-subtle)]/20 px-3 py-2.5">
            <p className="text-xs text-[var(--danger)]">
              {String(event.payload.detail ?? "执行出错")}
            </p>
          </div>
        </div>
      ))}

      {/* ── Confirmation cards ── */}
      {activeSession && pendingConfs.length > 0 ? (
        <div className="space-y-3">
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
                  if (activeSession) onSessionReload(activeSession.session_id);
                }}
                projectId={projectId}
                sessionId={activeSession.session_id}
              />
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

// ── Workspace Tabs ──────────────────────────────────────────────

function WorkspaceTabs({
  value,
  onChange,
}: {
  value: "super" | "target";
  onChange: (value: "super" | "target") => void;
}) {
  return (
    <div
      aria-label="对话模式"
      className="flex h-12 items-end gap-5 border-b border-[var(--hairline)] px-4"
      role="tablist"
    >
      <button
        aria-selected={value === "super"}
        className={`h-12 border-b-2 px-1 text-sm transition-colors ${
          value === "super"
            ? "border-[var(--ink)] font-medium text-[var(--ink)]"
            : "border-transparent text-[var(--muted)] hover:text-[var(--ink)]"
        }`}
        onClick={() => onChange("super")}
        role="tab"
        type="button"
      >
        超级 Agent
      </button>
      <button
        aria-selected={value === "target"}
        className={`h-12 border-b-2 px-1 text-sm transition-colors ${
          value === "target"
            ? "border-[var(--ink)] font-medium text-[var(--ink)]"
            : "border-transparent text-[var(--muted)] hover:text-[var(--ink)]"
        }`}
        onClick={() => onChange("target")}
        role="tab"
        type="button"
      >
        被测 Agent 对话
      </button>
    </div>
  );
}

// ── Message Bubble ──────────────────────────────────────────────

function ChatMessageBubble({
  isLastAssistant,
  message,
  isStreaming,
  onEdit,
  onRegenerate,
}: {
  isLastAssistant?: boolean;
  message: ChatMessage;
  isStreaming?: boolean;
  onEdit?: (newContent: string) => void;
  onRegenerate?: () => void;
}) {
  return (
    <UIMessageBubble
      animate
      content={message.content}
      isLastAssistant={isLastAssistant}
      isStreaming={isStreaming}
      onEdit={onEdit}
      onRegenerate={onRegenerate}
      role={message.role}
      timestamp={message.timestamp}
    />
  );
}

// ── Loading bar ─────────────────────────────────────────────────

function LoadingBar() {
  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-2 h-0.5 w-full overflow-hidden rounded-full bg-[var(--canvas-soft)]">
        <div className="h-full w-1/3 animate-[loading-bar_1.5s_ease-in-out_infinite] rounded-full bg-[var(--primary)]" />
      </div>
    </div>
  );
}
