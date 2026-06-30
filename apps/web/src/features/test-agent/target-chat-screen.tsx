"use client";

import { Bot, Send, User } from "lucide-react";
import { useEffect, useState } from "react";

import { listAgents, listAgentVersions } from "@/features/agents/api";
import { listEnvironmentTemplates } from "@/features/environments/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  createTargetChat,
  listTargetChats,
  sendTargetMessage,
  type TargetChatSession,
} from "./api";

type Option = { id: string; label: string };

export function TargetChatScreen({ projectId }: { projectId: string }) {
  const [versions, setVersions] = useState<Option[]>([]);
  const [environments, setEnvironments] = useState<Option[]>([]);
  const [versionId, setVersionId] = useState("");
  const [environmentId, setEnvironmentId] = useState("");
  const [session, setSession] = useState<TargetChatSession | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      listAgents(projectId),
      listEnvironmentTemplates(projectId),
      listTargetChats(projectId),
    ])
      .then(async ([agentPage, templates, history]) => {
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
              label: `${agent.name} · v${item.version_number}`,
            })),
        );
        setVersions(published);
        setVersionId(published[0]?.id ?? "");
        setEnvironments(
          templates.map((item) => ({ id: item.id, label: item.name })),
        );
        setSession(history.items[0] ?? null);
      })
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : "配置加载失败"),
      );
  }, [projectId]);

  async function ensureSession() {
    if (session) return session;
    if (!versionId) throw new Error("请先发布并选择一个被测 Agent 版本");
    const created = await createTargetChat(projectId, versionId, environmentId);
    setSession(created);
    return created;
  }

  async function send() {
    const content = input.trim();
    if (!content || sending) return;
    setSending(true);
    setError(null);
    try {
      const active = await ensureSession();
      const turn = await sendTargetMessage(
        projectId,
        active.session_id,
        content,
      );
      setSession({ ...active, turns: [...active.turns, turn] });
      setInput("");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "被测 Agent 调用失败",
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col">
      <div className="flex flex-wrap gap-3 border-b border-[var(--border)] p-4">
        <select
          aria-label="被测 Agent 版本"
          className="rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
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
          className="rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
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
        <Button onClick={() => setSession(null)} variant="secondary">
          新建测试会话
        </Button>
      </div>
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-5">
        {session?.turns.length ? (
          session.turns.map((turn) => (
            <div className="space-y-3" key={turn.turn_id}>
              <Bubble
                icon={<User className="size-4" />}
                text={String(turn.input.message ?? "")}
                user
              />
              <Bubble
                icon={<Bot className="size-4" />}
                text={JSON.stringify(turn.output, null, 2)}
              />
              <p className="pl-11 text-xs text-[var(--text-muted)]">
                耗时 {turn.duration_ms ?? "-"} ms · Trace{" "}
                {turn.trace?.length ?? 0} 条 · 评分 {turn.scores?.length ?? 0}{" "}
                项
              </p>
            </div>
          ))
        ) : (
          <p className="text-sm text-[var(--text-muted)]">
            选择版本后直接与真实被测 Agent 对话；每轮结果、Trace
            与耗时都会持久化。
          </p>
        )}
      </div>
      <div className="border-t border-[var(--border)] p-4">
        <div className="flex gap-2">
          <Input
            aria-label="被测 Agent 对话输入"
            onChange={(event) => setInput(event.target.value)}
            value={input}
          />
          <Button
            disabled={!input.trim() || sending}
            loading={sending}
            onClick={() => void send()}
            variant="primary"
          >
            <Send className="size-4" />
          </Button>
        </div>
        {error ? (
          <p className="mt-2 text-sm text-[var(--danger)]" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function Bubble({
  icon,
  text,
  user = false,
}: {
  icon: React.ReactNode;
  text: string;
  user?: boolean;
}) {
  return (
    <div className={`flex gap-3 ${user ? "flex-row-reverse" : ""}`}>
      <span className="flex size-8 items-center justify-center rounded-full bg-[var(--surface-subtle)]">
        {icon}
      </span>
      <pre className="max-w-[80%] whitespace-pre-wrap rounded-lg bg-[var(--surface)] px-4 py-3 text-sm">
        {text}
      </pre>
    </div>
  );
}
