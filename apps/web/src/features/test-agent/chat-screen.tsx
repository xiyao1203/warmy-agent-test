"use client";

import {
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Send,
  Sparkles,
  User,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import type { ChatMessage, ChatResponse } from "./api";
import { confirmPlan, sendChatMessage } from "./api";

export function TestAgentChat({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [planDraft, setPlanDraft] = useState<Record<string, unknown> | null>(
    null,
  );
  const [status, setStatus] = useState("active");
  const [sending, setSending] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || sending) return;
    const msg = input.trim();
    setInput("");
    setSending(true);
    try {
      const res: ChatResponse = await sendChatMessage(
        projectId,
        msg,
        sessionId ?? undefined,
      );
      setSessionId(res.session_id);
      setMessages(res.messages);
      setPlanDraft(
        Object.keys(res.plan_draft).length > 0 ? res.plan_draft : null,
      );
      setStatus(res.status);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "抱歉，处理失败，请重试。", timestamp: new Date().toISOString() },
      ]);
    } finally {
      setSending(false);
    }
  }

  async function handleConfirm() {
    if (!sessionId) return;
    setConfirming(true);
    try {
      const res = await confirmPlan(projectId, sessionId);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.message, timestamp: new Date().toISOString() },
      ]);
      setStatus(res.status);
      setPlanDraft(null);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "确认失败，请重试。", timestamp: new Date().toISOString() },
      ]);
    } finally {
      setConfirming(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      {/* Header */}
      <header className="flex items-center gap-3 border-b border-[var(--border)] px-6 py-4">
        <Sparkles className="size-5 text-[var(--accent)]" />
        <div>
          <h1 className="text-lg font-semibold">测试 Agent</h1>
          <p className="text-xs text-[var(--text-muted)]">
            用自然语言描述测试需求，Agent 为您生成测试计划。
          </p>
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center">
            <Bot className="size-12 text-[var(--text-muted)]" />
            <p className="mt-4 text-sm font-medium text-[var(--text-muted)]">
              告诉我您想测试什么
            </p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              例如：&ldquo;测试登录流程，使用 admin 账号&rdquo;
            </p>
          </div>
        ) : (
          <div className="mx-auto max-w-2xl space-y-4">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            {planDraft ? (
              <PlanCard
                onConfirm={handleConfirm}
                confirming={confirming}
                plan={planDraft}
              />
            ) : null}
            {status === "confirmed" || status === "completed" ? (
              <div className="flex items-center gap-2 rounded border border-[var(--success)] bg-[var(--success-subtle)] px-4 py-3 text-sm">
                <CheckCircle2 className="size-4 text-[var(--success)]" />
                测试计划已确认执行
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-[var(--border)] px-6 py-4">
        <div className="mx-auto flex max-w-2xl gap-2">
          <Input
            className="flex-1"
            disabled={sending || status === "completed"}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="描述您的测试需求..."
            value={input}
          />
          <Button
            disabled={sending || !input.trim() || status === "completed"}
            loading={sending}
            onClick={handleSend}
            variant="primary"
          >
            <Send className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex size-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-[var(--accent)] text-white"
            : "bg-[var(--surface-subtle)] text-[var(--text)]"
        }`}
      >
        {isUser ? (
          <User className="size-4" />
        ) : (
          <Bot className="size-4" />
        )}
      </div>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
          isUser
            ? "bg-[var(--accent)] text-white"
            : "bg-[var(--surface-subtle)] text-[var(--text)]"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}

function PlanCard({
  confirming,
  onConfirm,
  plan,
}: {
  confirming: boolean;
  onConfirm: () => Promise<void>;
  plan: Record<string, unknown>;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-[var(--accent)] bg-[var(--surface)] p-4">
      <button
        className="flex w-full items-center gap-2 text-left"
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <Sparkles className="size-4 text-[var(--accent)]" />
        <span className="flex-1 text-sm font-semibold">
          测试计划草稿
        </span>
        {expanded ? (
          <ChevronDown className="size-4" />
        ) : (
          <ChevronRight className="size-4" />
        )}
      </button>
      {expanded ? (
        <div className="mt-3 space-y-2 text-xs">
          {Object.entries(plan).map(([key, value]) => (
            <div className="flex justify-between gap-2" key={key}>
              <span className="text-[var(--text-muted)]">{key}</span>
              <span className="text-right font-mono">
                {value === null ? "未指定" : String(value)}
              </span>
            </div>
          ))}
        </div>
      ) : null}
      <div className="mt-3 flex justify-end">
        <Button
          disabled={confirming}
          loading={confirming}
          onClick={onConfirm}
          variant="primary"
        >
          <CheckCircle2 className="mr-1.5 size-4" />
          确认执行
        </Button>
      </div>
    </div>
  );
}
