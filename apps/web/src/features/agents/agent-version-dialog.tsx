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

type AgentVersionDialogProps = {
  triggerLabel: string;
  version?: AgentVersionResponse;
  onSubmit: (payload: CreateAgentVersionRequest) => Promise<unknown>;
};

export function AgentVersionDialog({
  onSubmit,
  triggerLabel,
  version,
}: AgentVersionDialogProps) {
  const config = version?.config ?? {};
  const [open, setOpen] = useState(false);
  const [apiUrl, setApiUrl] = useState(String(config.api_url ?? ""));
  const [model, setModel] = useState(String(config.model ?? ""));
  const [timeout, setTimeout] = useState(Number(config.timeout ?? 30));
  const [protocol, setProtocol] = useState<InvocationProtocol>(
    (config.protocol as InvocationProtocol) ?? "sync_json",
  );
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
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!apiUrl.trim()) {
      setError("请输入 API 地址");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const parsedTemplate = JSON.parse(requestTemplate) as unknown;
      if (
        !parsedTemplate ||
        typeof parsedTemplate !== "object" ||
        Array.isArray(parsedTemplate)
      ) {
        setError("请求模板必须是 JSON 对象");
        return;
      }
      await onSubmit({
        config: {
          api_url: apiUrl.trim(),
          model: model.trim() || null,
          protocol,
          request_template: parsedTemplate as Record<string, unknown>,
          response_path: responsePath.trim(),
          timeout,
        },
      });
      setOpen(false);
    } catch (caught) {
      setError(
        caught instanceof SyntaxError
          ? "请求模板不是合法 JSON"
          : "保存版本失败，请检查配置后重试。",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant={version ? "secondary" : "primary"}>
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>
          {version ? "编辑 Agent 版本" : "创建 Agent 版本"}
        </DialogTitle>
        <DialogDescription>
          配置真实调用协议、请求映射、响应提取和执行限制。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            API 地址
            <Input
              className="mt-1.5"
              onChange={(event) => setApiUrl(event.target.value)}
              placeholder="https://agent.example.com"
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
              <option value="sync_json">同步 JSON</option>
              <option value="openai_chat">OpenAI Chat Compatible</option>
              <option value="sse">SSE 流式</option>
              <option value="async_poll">异步轮询</option>
            </select>
          </label>
          <label className="block text-sm font-medium">
            请求模板（JSON）
            <textarea
              className="mt-1.5 min-h-28 w-full rounded border border-[var(--border)] bg-[var(--surface)] p-3 font-mono text-xs"
              onChange={(event) => setRequestTemplate(event.target.value)}
              value={requestTemplate}
            />
          </label>
          <label className="block text-sm font-medium">
            响应提取路径
            <Input
              className="mt-1.5"
              onChange={(event) => setResponsePath(event.target.value)}
              placeholder="choices.0.message.content"
              value={responsePath}
            />
          </label>
          <label className="block text-sm font-medium">
            模型
            <Input
              className="mt-1.5"
              onChange={(event) => setModel(event.target.value)}
              placeholder="可选"
              value={model}
            />
          </label>
          <label className="block text-sm font-medium">
            超时（秒）
            <Input
              className="mt-1.5"
              min={1}
              onChange={(event) => setTimeout(Number(event.target.value))}
              type="number"
              value={timeout}
            />
          </label>
          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}
          <div className="flex justify-end gap-2">
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
      </DialogContent>
    </Dialog>
  );
}
