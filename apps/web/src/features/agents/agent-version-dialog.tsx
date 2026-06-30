"use client";

import type {
  AgentVersionResponse,
  CreateAgentVersionRequest,
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
      await onSubmit({
        config: {
          api_url: apiUrl.trim(),
          model: model.trim() || null,
          timeout,
        },
      });
      setOpen(false);
    } catch {
      setError("保存版本失败，请检查配置后重试。");
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
          配置通用 HTTP Agent 的调用地址、模型和超时。
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
