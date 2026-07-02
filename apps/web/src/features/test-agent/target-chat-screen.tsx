"use client";

import { CornerDownLeft, RefreshCw, StopCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  ChatEmptyState,
  FollowUpChips,
  MessageBubble,
  TypingIndicator,
} from "@/components/uiverse";

import { listAgents, listAgentVersions } from "@/features/agents/api";
import { listEnvironmentTemplates } from "@/features/environments/api";

import {
  createTargetChat,
  listTargetChats,
  sendTargetMessage,
  type TargetChatSession,
  type TargetChatTurn,
} from "./api";

type Option = { id: string; label: string };

export function TargetChatScreen({ projectId }: { projectId: string }) {
  const [versions, setVersions] = useState<Option[]>([]);
  const [environments, setEnvironments] = useState<Option[]>([]);
  const [versionId, setVersionId] = useState("");
  const [environmentId, setEnvironmentId] = useState("");
  const [session, setSession] = useState<TargetChatSession | null>(null);
  const [turns, setTurns] = useState<TargetChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingInit, setLoadingInit] = useState(true);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const pinnedBottomRef = useRef(true);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    let alive = true;
    listTargetChats(projectId)
      .then(async (history) => {
        if (!alive) return;
        const [agentPage, templates] = await Promise.all([
          listAgents(projectId),
          listEnvironmentTemplates(projectId),
        ]);
        if (!alive) return;

        const agents = agentPage.items;
        const groups = await Promise.all(
          agents.map(async (agent) => ({
            agent,
            versions: await listAgentVersions(projectId, agent.id),
          })),
        );
        const published = groups.flatMap(({ agent, versions: items }) =>
          items
            .filter((item) => item.status === "published")
            .map((item) => ({
              id: item.id,
              label: `${agent.name} \u00b7 v${item.version_number}`,
            })),
        );
        setVersions(published);
        setVersionId(published[0]?.id ?? "");
        setEnvironments(
          templates.map((item) => ({ id: item.id, label: item.name })),
        );

        const latest = history.items[0] ?? null;
        if (latest) {
          setSession(latest);
          setTurns(latest.turns);
        }
      })
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : "配置加载失败"),
      )
      .finally(() => {
        if (alive) setLoadingInit(false);
      });
    return () => {
      alive = false;
    };
  }, [projectId]);

  useEffect(() => {
    if (!loadingInit) inputRef.current?.focus();
  }, [loadingInit]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || !pinnedBottomRef.current) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [turns, sending]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const threshold = 80;
    pinnedBottomRef.current =
      el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
  }, []);

  async function ensureSession(): Promise<TargetChatSession> {
    if (session) return session;
    if (!versionId) throw new Error("请先发布并选择一个被测 Agent 版本");
    const created = await createTargetChat(projectId, versionId, environmentId);
    setSession(created);
    return created;
  }

  function stop() {
    abortRef.current?.abort();
    abortRef.current = null;
    setSending(false);
  }

  async function send() {
    const content = input.trim();
    if (!content || sending) return;
    setInput("");
    setSending(true);
    setError(null);
    pinnedBottomRef.current = true;

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const active = await ensureSession();
      const turn = await sendTargetMessage(
        projectId,
        active.session_id,
        content,
        ctrl.signal,
      );
      setTurns((cur) => [...cur, turn]);
      setSession((cur) =>
        cur ? { ...cur, turns: [...cur.turns, turn] } : cur,
      );
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      setError(
        reason instanceof Error ? reason.message : "被测 Agent 调用失败",
      );
    } finally {
      setSending(false);
      abortRef.current = null;
      inputRef.current?.focus();
    }
  }

  function extractOutputText(
    output: Record<string, unknown> | null | undefined,
  ): string {
    if (!output) return "";
    if (typeof output.message === "string") return output.message;
    if (typeof output.content === "string") return output.content;
    if (typeof output.text === "string") return output.text;
    if (typeof output.response === "string") return output.response;
    return JSON.stringify(output, null, 2);
  }

  function extractErrorText(
    err: Record<string, unknown> | null | undefined,
  ): string {
    if (!err) return "调用失败";
    const msg = err.message ?? err.detail ?? err.error;
    return typeof msg === "string" ? msg : JSON.stringify(err);
  }

  const versionLabel = versions.find((v) => v.id === versionId)?.label;
  const hasSession = session !== null && turns.length > 0;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden bg-[var(--canvas)]">
      <header className="flex shrink-0 items-center gap-3 border-b border-[var(--hairline)] px-4 py-2.5">
        <select
          aria-label="被测 Agent 版本"
          className="min-w-0 flex-1 rounded-lg border border-[var(--hairline)] bg-[var(--surface)] px-3 py-1.5 text-[0.8125rem] text-[var(--ink)]"
          disabled={Boolean(session)}
          onChange={(event) => setVersionId(event.target.value)}
          value={versionId}
        >
          <option value="">选择已发布 Agent 版本</option>
          {versions.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
        <select
          aria-label="测试环境"
          className="min-w-0 flex-1 rounded-lg border border-[var(--hairline)] bg-[var(--surface)] px-3 py-1.5 text-[0.8125rem] text-[var(--ink)]"
          disabled={Boolean(session)}
          onChange={(event) => setEnvironmentId(event.target.value)}
          value={environmentId}
        >
          <option value="">无环境模板</option>
          {environments.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
        {hasSession ? (
          <button
            aria-label="新建测试会话"
            className="shrink-0 rounded-lg p-1.5 text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
            onClick={() => {
              setSession(null);
              setTurns([]);
              setError(null);
            }}
            title="新建测试会话"
            type="button"
          >
            <RefreshCw className="size-4" />
          </button>
        ) : null}
      </header>

      <div
        className="chat-scroll min-h-0 flex-1 overflow-y-auto px-5 py-4"
        onScroll={handleScroll}
        ref={scrollRef}
      >
        {loadingInit ? (
          <div className="mx-auto max-w-3xl">
            <div className="mb-2 h-0.5 w-full overflow-hidden rounded-full bg-[var(--canvas-soft)]">
              <div className="h-full w-1/3 animate-[loading-bar_1.5s_ease-in-out_infinite] rounded-full bg-[var(--primary)]" />
            </div>
          </div>
        ) : !hasSession ? (
          <ChatEmptyState
            description={versionLabel
              ? `已选择 ${versionLabel}，发送消息开始测试`
              : "选择一个已发布的 Agent 版本，然后发送消息开始对话测试"}
            onSuggestionClick={setInput}
            suggestions={versionLabel
              ? ["你好，介绍一下你自己", "你能做什么？", "帮我完成一个简单任务"]
              : []}
            title="被测 Agent 对话"
          />
        ) : (
          <div className="mx-auto max-w-3xl">
            {turns.map((turn) => {
              const userContent = String(
                (turn.input as Record<string, unknown>).message ?? "",
              );
              const assistantContent = turn.error
                ? `调用失败: ${extractErrorText(turn.error)}`
                : extractOutputText(turn.output);

              return (
                <div className="mb-8 last:mb-0" key={turn.turn_id}>
                  <MessageBubble
                    content={userContent}
                    role="user"
                    timestamp={turn.created_at}
                  />
                  <div className="mt-6">
                    <MessageBubble
                      content={assistantContent}
                      role="assistant"
                      timestamp={turn.created_at}
                    />
                  </div>
                  <div className="mt-1.5 pl-11 text-[0.65rem] text-[var(--muted)]">
                    耗时 {turn.duration_ms ?? "-"} ms
                    {turn.trace?.length
                      ? ` \u00b7 Trace ${turn.trace.length} 条`
                      : ""}
                    {turn.scores?.length
                      ? ` \u00b7 评分 ${turn.scores.length} 项`
                      : ""}
                    {turn.token_usage
                      ? ` \u00b7 Token ${JSON.stringify(turn.token_usage)}`
                      : null}
                  </div>
                </div>
              );
            })}

            {sending ? (
              <div className="mb-8">
                <TypingIndicator />
              </div>
            ) : turns.length > 0 ? (
              <FollowUpChips
                items={[
                  "再试一次",
                  "能详细说明一下吗？",
                  "换个方式回答",
                ]}
                onClick={setInput}
              />
            ) : null}
          </div>
        )}
      </div>

      {error ? (
        <div
          className="shrink-0 border-t border-[var(--danger)]/30 bg-[var(--danger-subtle)]/20 px-4 py-2.5"
          role="alert"
        >
          <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
            <p className="min-w-0 flex-1 text-xs text-[var(--danger)]">
              {error}
            </p>
            <button
              className="shrink-0 rounded px-2 py-0.5 text-xs text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
              onClick={() => setError(null)}
              type="button"
            >
              关闭
            </button>
          </div>
        </div>
      ) : null}

      <div className="shrink-0 border-t border-[var(--hairline)] px-4 py-3">
        {/* Context window indicator */}
        <div className="mx-auto mb-2 flex max-w-3xl items-center gap-2">
          <div className="h-1 flex-1 overflow-hidden rounded-full bg-[var(--canvas-soft)]">
            <div
              className="h-full rounded-full bg-[var(--primary)]/40 transition-all"
              style={{ width: `${Math.min(100, turns.length * 10)}%` }}
            />
          </div>
          <span className="shrink-0 text-[0.6rem] text-[var(--muted)]">
            {turns.length > 0 ? `${turns.length} 轮对话` : "新对话"}
          </span>
        </div>
        <div className="mx-auto flex max-w-3xl gap-2">
          <div className="relative flex-1">
            <textarea
              aria-label="被测 Agent 对话输入"
              className="w-full resize-none rounded-2xl border border-[var(--hairline)] bg-[var(--canvas-soft)] px-4 py-3 pr-10 text-[0.9375rem] leading-6 text-[var(--ink)] placeholder-[var(--muted)] transition-shadow focus:border-[var(--hairline-strong)] focus:shadow-md focus:outline-none disabled:opacity-50"
              disabled={sending}
              onChange={(event) => {
                setInput(event.target.value);
                const el = event.target;
                el.style.height = "auto";
                el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void send();
                }
              }}
              placeholder="向被测 Agent 发送消息…"
              ref={inputRef}
              rows={1}
              value={input}
            />
            {sending ? (
              <button
                aria-label="停止"
                className="absolute bottom-2 right-2 rounded-lg p-1.5 text-[var(--muted)] transition-colors hover:bg-[var(--danger-subtle)] hover:text-[var(--danger)]"
                onClick={stop}
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
                onClick={() => void send()}
                type="button"
              >
                <CornerDownLeft className="size-5" />
              </button>
            )}
          </div>
        </div>
        <p className="mx-auto mt-2 max-w-3xl text-center text-[0.65rem] text-[var(--muted)]">
          被测 Agent 回复由目标模型生成，结果可能不准确。
        </p>
      </div>
    </div>
  );
}
