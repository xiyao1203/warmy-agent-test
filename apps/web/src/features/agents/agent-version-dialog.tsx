"use client";

import type {
  AgentVersionResponse,
  CreateAgentVersionRequest,
  InvocationProtocol,
} from "@warmy/generated-api-client";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ConnectionTestPanel } from "./connection-test-panel";

type AgentVersionDialogProps = {
  triggerLabel: string;
  version?: AgentVersionResponse;
  projectId: string;
  agentId: string;
  onSubmit: (payload: CreateAgentVersionRequest) => Promise<void>;
};

const PROTOCOL_LABELS: Record<InvocationProtocol, string> = {
  async_poll: "异步轮询",
  openai_chat: "OpenAI Chat Compatible",
  sse: "SSE 流式",
  sync_json: "同步 JSON",
};

type Section = "connection" | "mappings" | "limits" | "metadata";

const SECTION_LABELS: Record<Section, string> = {
  connection: "连接",
  limits: "限制",
  mappings: "映射",
  metadata: "元数据",
};

const ALL_SECTIONS: Section[] = [
  "connection",
  "mappings",
  "limits",
  "metadata",
];

export function AgentVersionDialog({
  agentId,
  onSubmit,
  projectId,
  triggerLabel,
  version,
}: AgentVersionDialogProps) {
  const config = version?.config ?? {};
  const [open, setOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<Section>("connection");

  // ── 连接 ──
  const [apiUrl, setApiUrl] = useState(String(config.api_url ?? ""));
  const [protocol, setProtocol] = useState<InvocationProtocol>(
    (config.protocol as InvocationProtocol) ?? "sync_json",
  );

  // ── 映射 ──
  const [responsePath, setResponsePath] = useState(
    String(config.response_path ?? "output"),
  );
  const [requestTemplate, setRequestTemplate] = useState(
    JSON.stringify(
      config.request_template ?? { input: "{{ input }}" },
      null,
      2,
    ),
  );

  // ── 限制 ──
  const [timeout, setTimeoutVal] = useState(Number(config.timeout ?? 30));
  const [maxSteps, setMaxSteps] = useState(
    config.max_steps != null ? String(config.max_steps) : "",
  );
  const [costLimit, setCostLimit] = useState(
    config.cost_limit != null ? String(config.cost_limit) : "",
  );

  // ── 元数据 ──
  const [model, setModel] = useState(String(config.model ?? ""));
  const [systemPrompt, setSystemPrompt] = useState(
    String(config.system_prompt ?? ""),
  );
  const [codeVersion, setCodeVersion] = useState(
    String(config.code_version ?? ""),
  );
  const [gitCommit, setGitCommit] = useState(String(config.git_commit ?? ""));

  // ── 提交状态 ──
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!apiUrl.trim()) {
      setError("请输入 API 地址");
      return;
    }

    let parsedTemplate: Record<string, unknown>;
    try {
      const raw = JSON.parse(requestTemplate) as unknown;
      if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
        setError("请求模板必须是 JSON 对象");
        return;
      }
      parsedTemplate = raw as Record<string, unknown>;
    } catch {
      setError("请求模板不是合法 JSON");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const payload: CreateAgentVersionRequest = {
        config: {
          api_url: apiUrl.trim(),
          protocol,
          request_template: parsedTemplate,
          response_path: responsePath.trim(),
          timeout,
          model: model.trim() || undefined,
          system_prompt: systemPrompt.trim() || undefined,
          code_version: codeVersion.trim() || undefined,
          git_commit: gitCommit.trim() || undefined,
          max_steps: maxSteps ? Number(maxSteps) : undefined,
          cost_limit: costLimit ? Number(costLimit) : undefined,
        },
      };
      await onSubmit(payload);
      setOpen(false);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "保存版本失败，请检查配置后重试。",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const isEditing = version != null;

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant={version ? "secondary" : "primary"}>
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-auto">
        <DialogTitle>
          {isEditing ? "编辑 Agent 版本" : "创建 Agent 版本"}
        </DialogTitle>
        <DialogDescription>
          配置真实调用协议、请求映射、响应提取和执行限制。标有 &ldquo;仅 Trace
          记录&rdquo;的字段不影响执行行为。
        </DialogDescription>

        {/* ── 分段 Tab ── */}
        <div className="mt-4 flex gap-1 border-b border-[var(--border)]">
          {ALL_SECTIONS.map((s) => (
            <button
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                activeSection === s
                  ? "border-b-2 border-[var(--accent)] text-[var(--accent)]"
                  : "text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
              key={s}
              onClick={() => setActiveSection(s)}
              type="button"
            >
              {SECTION_LABELS[s]}
            </button>
          ))}
        </div>

        <div className="mt-4 space-y-4">
          {/* ── 1. 连接 ── */}
          {activeSection === "connection" ? (
            <>
              <label className="block text-sm font-medium">
                API 地址 *
                <Input
                  className="mt-1.5"
                  onChange={(event) => setApiUrl(event.target.value)}
                  placeholder="https://agent.example.com/api"
                  value={apiUrl}
                />
              </label>
              <label className="block text-sm font-medium">
                调用协议
                <select
                  className="mt-1.5 h-9 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3"
                  onChange={(event) =>
                    setProtocol(event.target.value as InvocationProtocol)
                  }
                  value={protocol}
                >
                  {(
                    Object.entries(PROTOCOL_LABELS) as [
                      InvocationProtocol,
                      string,
                    ][]
                  ).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>

              {/* 连接测试面板 */}
              {isEditing && version.status === "draft" ? (
                <ConnectionTestPanel
                  agentId={agentId}
                  projectId={projectId}
                  version={version}
                  versionId={version.id}
                />
              ) : (
                <p className="text-xs text-[var(--muted)]">
                  保存版本后可使用连接测试面板验证 Agent 连通性。
                </p>
              )}
            </>
          ) : null}

          {/* ── 2. 映射 ── */}
          {activeSection === "mappings" ? (
            <>
              <label className="block text-sm font-medium">
                请求模板（JSON，支持 {"{{ input }}"} 占位）
                <textarea
                  className="mt-1.5 min-h-32 w-full rounded border border-[var(--border)] bg-[var(--surface)] p-3 font-mono text-xs"
                  onChange={(event) => setRequestTemplate(event.target.value)}
                  value={requestTemplate}
                />
              </label>
              <label className="block text-sm font-medium">
                响应提取路径
                <Input
                  className="mt-1.5"
                  onChange={(event) => setResponsePath(event.target.value)}
                  placeholder="例如 choices.0.message.content"
                  value={responsePath}
                />
                <span className="mt-1 text-xs text-[var(--muted)]">
                  从 Agent 响应 JSON
                  中提取实际输出的路径，支持点号分隔的嵌套字段。
                </span>
              </label>
            </>
          ) : null}

          {/* ── 3. 限制 ── */}
          {activeSection === "limits" ? (
            <>
              <label className="block text-sm font-medium">
                超时（秒，1–600）
                <Input
                  className="mt-1.5"
                  min={1}
                  max={600}
                  onChange={(event) =>
                    setTimeoutVal(Number(event.target.value))
                  }
                  type="number"
                  value={timeout}
                />
              </label>
              <label className="block text-sm font-medium">
                最大步数（可选）
                <Input
                  className="mt-1.5"
                  min={1}
                  onChange={(event) => setMaxSteps(event.target.value)}
                  placeholder="不限制"
                  type="number"
                  value={maxSteps}
                />
                <span className="mt-1 text-xs text-[var(--muted)]">
                  多步 Agent 的执行步数上限。
                </span>
              </label>
              <label className="block text-sm font-medium">
                成本上限（可选，USD）
                <Input
                  className="mt-1.5"
                  min={0}
                  onChange={(event) => setCostLimit(event.target.value)}
                  placeholder="不限制"
                  step="0.01"
                  type="number"
                  value={costLimit}
                />
                <span className="mt-1 text-xs text-[var(--muted)]">
                  单次运行的成本上限，超出后自动停止。
                </span>
              </label>
            </>
          ) : null}

          {/* ── 4. 元数据 ── */}
          {activeSection === "metadata" ? (
            <>
              <label className="block text-sm font-medium">
                模型
                <Input
                  className="mt-1.5"
                  onChange={(event) => setModel(event.target.value)}
                  placeholder="例如 gpt-4o（仅 Trace 记录）"
                  value={model}
                />
                <span className="mt-1 text-xs text-[var(--muted)]">
                  仅 Trace 记录，不影响执行行为。
                </span>
              </label>
              <label className="block text-sm font-medium">
                系统提示词
                <textarea
                  className="mt-1.5 min-h-20 w-full rounded border border-[var(--border)] bg-[var(--surface)] p-3 text-xs"
                  onChange={(event) => setSystemPrompt(event.target.value)}
                  placeholder="（仅 Trace 记录）"
                  value={systemPrompt}
                />
                <span className="mt-1 text-xs text-[var(--muted)]">
                  仅 Trace 记录，不影响执行行为。
                </span>
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="block text-sm font-medium">
                  代码版本
                  <Input
                    className="mt-1.5"
                    onChange={(event) => setCodeVersion(event.target.value)}
                    placeholder="v1.2.0（仅 Trace）"
                    value={codeVersion}
                  />
                </label>
                <label className="block text-sm font-medium">
                  Git Commit
                  <Input
                    className="mt-1.5"
                    onChange={(event) => setGitCommit(event.target.value)}
                    placeholder="abc1234（仅 Trace）"
                    value={gitCommit}
                  />
                </label>
              </div>
            </>
          ) : null}

          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}

          {/* ── 底部操作栏 ── */}
          <div className="flex items-center justify-between border-t border-[var(--border)] pt-4">
            <div className="flex gap-1">
              {ALL_SECTIONS.map((s, i) => (
                <span
                  className={`text-xs ${
                    activeSection === s
                      ? "text-[var(--foreground)]"
                      : "text-[var(--muted)]"
                  }`}
                  key={s}
                >
                  {SECTION_LABELS[s]}
                  {i < ALL_SECTIONS.length - 1 ? " · " : ""}
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setOpen(false)} type="button">
                取消
              </Button>
              <Button
                disabled={submitting}
                onClick={submit}
                type="button"
                variant="primary"
              >
                {submitting ? "保存中…" : "保存版本"}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
