"use client";

import {
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Send,
  Sparkles,
  User,
  Play,
  FileCode,
  Wrench,
  Loader2,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatEmptyState, TypingIndicator, Tooltip } from "@/components/uiverse";

import type {
  ChatMessage,
  ChatResponse,
  PlaywrightAgentTask,
  PlaywrightAgentRequest,
} from "./api";
import {
  confirmPlan,
  sendChatMessage,
  executePlaywrightAgent,
  TestAgentApiError,
} from "./api";

export function TestAgentChat({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [planDraft, setPlanDraft] = useState<Record<string, unknown> | null>(
    null,
  );
  const [status, setStatus] = useState("active");
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState<{
    message: string;
    needsModel: boolean;
  } | null>(null);
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
    setChatError(null);
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
    } catch (error) {
      setInput(msg);
      setChatError({
        message: error instanceof Error ? error.message : "处理失败，请重试。",
        needsModel: error instanceof TestAgentApiError && error.status === 409,
      });
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
        {
          role: "assistant",
          content: res.message,
          timestamp: new Date().toISOString(),
        },
      ]);
      setStatus(res.status);
      setPlanDraft(null);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "确认失败，请重试。",
          timestamp: new Date().toISOString(),
        },
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
          <ChatEmptyState
            onSuggestionClick={(suggestion) => {
              setInput(suggestion);
            }}
            suggestions={[
              "测试登录流程，使用 admin 账号",
              "验证用户注册表单的必填字段",
              "检查购物车添加和删除功能",
            ]}
          />
        ) : (
          <div className="mx-auto max-w-2xl space-y-4">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            {sending ? (
              <div className="flex gap-3">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[var(--surface-subtle)]">
                  <Bot className="size-4" />
                </div>
                <TypingIndicator />
              </div>
            ) : null}
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
          <Tooltip content="发送消息 (Enter)">
            <Button
              disabled={sending || !input.trim() || status === "completed"}
              loading={sending}
              onClick={handleSend}
              variant="primary"
            >
              <Send className="size-4" />
            </Button>
          </Tooltip>
        </div>
        {chatError ? (
          <div
            className="mx-auto mt-2 flex max-w-2xl items-center justify-between gap-3 rounded-[var(--radius-sm)] border border-[var(--danger)] bg-[var(--danger-subtle)] px-3 py-2 text-sm text-[var(--danger)]"
            role="alert"
          >
            <span>{chatError.message}</span>
            {chatError.needsModel ? (
              <Button asChild variant="secondary">
                <Link href={`/projects/${projectId}/models`}>配置模型</Link>
              </Button>
            ) : null}
          </div>
        ) : null}
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
        {isUser ? <User className="size-4" /> : <Bot className="size-4" />}
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
        <span className="flex-1 text-sm font-semibold">测试计划草稿</span>
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

// ── Playwright Agent Panel ────────────────────────────────────────────────────

export function PlaywrightAgentPanel({ projectId }: { projectId: string }) {
  const [agentType, setAgentType] = useState<
    "planner" | "generator" | "healer"
  >("planner");
  const [prompt, setPrompt] = useState("");
  const [planPath, setPlanPath] = useState("");
  const [testName, setTestName] = useState("");
  const [executing, setExecuting] = useState(false);
  const [task, setTask] = useState<PlaywrightAgentTask | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleExecute() {
    if (!prompt.trim() || executing) return;
    setExecuting(true);
    setError(null);
    setTask(null);

    try {
      const request: PlaywrightAgentRequest = {
        agent_type: agentType,
        prompt: prompt.trim(),
      };

      if (agentType === "generator" && planPath.trim()) {
        request.plan_path = planPath.trim();
      }
      if (agentType === "healer" && testName.trim()) {
        request.test_name = testName.trim();
      }

      const result = await executePlaywrightAgent(projectId, request);
      setTask(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "执行失败");
    } finally {
      setExecuting(false);
    }
  }

  const agentIcons = {
    planner: <Play className="size-4" />,
    generator: <FileCode className="size-4" />,
    healer: <Wrench className="size-4" />,
  };

  const agentLabels = {
    planner: "Planner",
    generator: "Generator",
    healer: "Healer",
  };

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
      <h3 className="mb-3 text-sm font-semibold text-[var(--text)]">
        Playwright Test Agents
      </h3>

      {/* Agent Type Selector */}
      <div className="mb-3 flex gap-2">
        {(["planner", "generator", "healer"] as const).map((type) => (
          <button
            key={type}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              agentType === type
                ? "bg-[var(--accent)] text-white"
                : "bg-[var(--surface-subtle)] text-[var(--text-muted)] hover:bg-[var(--border)]"
            }`}
            onClick={() => setAgentType(type)}
            type="button"
          >
            {agentIcons[type]}
            {agentLabels[type]}
          </button>
        ))}
      </div>

      {/* Prompt Input */}
      <div className="mb-3">
        <Input
          className="w-full"
          disabled={executing}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={
            agentType === "planner"
              ? "描述要测试的功能..."
              : agentType === "generator"
                ? "输入测试计划内容..."
                : "输入失败的测试名称..."
          }
          value={prompt}
        />
      </div>

      {/* Conditional Inputs */}
      {agentType === "generator" && (
        <div className="mb-3">
          <Input
            className="w-full"
            disabled={executing}
            onChange={(e) => setPlanPath(e.target.value)}
            placeholder="测试计划文件路径（可选）"
            value={planPath}
          />
        </div>
      )}

      {agentType === "healer" && (
        <div className="mb-3">
          <Input
            className="w-full"
            disabled={executing}
            onChange={(e) => setTestName(e.target.value)}
            placeholder="失败的测试名称"
            value={testName}
          />
        </div>
      )}

      {/* Execute Button */}
      <Tooltip
        content={
          executing ? "正在执行中..." : `执行 ${agentLabels[agentType]} Agent`
        }
      >
        <Button
          className="w-full"
          disabled={executing || !prompt.trim()}
          loading={executing}
          onClick={handleExecute}
          variant="primary"
        >
          {executing ? (
            <>
              <Loader2 className="mr-1.5 size-4 animate-spin" />
              执行中...
            </>
          ) : (
            <>
              <Play className="mr-1.5 size-4" />
              执行 {agentLabels[agentType]}
            </>
          )}
        </Button>
      </Tooltip>

      {/* Error Display */}
      {error && (
        <div className="mt-3 flex items-center gap-2 rounded border border-[var(--error)] bg-[var(--error-subtle)] px-3 py-2 text-xs text-[var(--error)]">
          <XCircle className="size-3.5 shrink-0" />
          {error}
        </div>
      )}

      {/* Task Result */}
      {task && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center gap-2">
            {task.status === "completed" ? (
              <CheckCircle className="size-4 text-[var(--success)]" />
            ) : task.status === "failed" ? (
              <XCircle className="size-4 text-[var(--error)]" />
            ) : (
              <Loader2 className="size-4 animate-spin text-[var(--accent)]" />
            )}
            <span className="text-xs font-medium">任务 {task.task_id}</span>
            <Badge
              tone={
                task.status === "completed"
                  ? "success"
                  : task.status === "failed"
                    ? "danger"
                    : "neutral"
              }
            >
              {task.status}
            </Badge>
          </div>

          {task.output && (
            <div className="rounded bg-[var(--surface-subtle)] p-2 text-xs">
              <pre className="whitespace-pre-wrap break-words">
                {task.output}
              </pre>
            </div>
          )}

          {task.artifacts && task.artifacts.length > 0 && (
            <div className="space-y-1">
              <span className="text-xs font-medium text-[var(--text-muted)]">
                生成的文件：
              </span>
              {task.artifacts.map((file, i) => (
                <div className="flex items-center gap-1.5 text-xs" key={i}>
                  <FileCode className="size-3.5 text-[var(--accent)]" />
                  <span className="font-mono">{file}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
