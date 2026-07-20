"use client";

import type { AgentVersionResponse } from "@warmy/generated-api-client";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { validateAgentConnection } from "./api";

type ConnectionTestPanelProps = {
  projectId: string;
  agentId: string;
  versionId: string;
  version: AgentVersionResponse;
  disabled?: boolean;
};

type TestResult = {
  ok: boolean;
  status_code: number;
  latency_ms: number;
  response_preview: unknown;
} | null;

export function ConnectionTestPanel({
  agentId,
  disabled,
  projectId,
  version,
  versionId,
}: ConnectionTestPanelProps) {
  const [probeInput, setProbeInput] = useState('{\n  "message": "hello"\n}');
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<TestResult>(null);
  const [error, setError] = useState("");

  async function handleTest() {
    setTesting(true);
    setResult(null);
    setError("");

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(probeInput) as Record<string, unknown>;
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        setError("探测输入必须是 JSON 对象");
        setTesting(false);
        return;
      }
    } catch {
      setError("探测输入不是合法 JSON");
      setTesting(false);
      return;
    }

    try {
      const data = await validateAgentConnection(
        projectId,
        agentId,
        versionId,
        parsed,
      );
      setResult(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "连接测试失败");
    } finally {
      setTesting(false);
    }
  }

  const config = version.config ?? {};

  return (
    <div className="space-y-4 rounded border border-[var(--hairline)] p-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold">连接测试</h4>
          <p className="text-xs text-[var(--muted)]">
            向 {String(config.api_url ?? "未配置")} 发送探测请求
          </p>
        </div>
        <Button
          disabled={disabled ?? testing}
          onClick={handleTest}
          variant="secondary"
        >
          {testing ? "测试中…" : "测试连接"}
        </Button>
      </div>

      <label className="block text-sm font-medium">
        探测输入（JSON）
        <textarea
          className="text-code mt-1.5 min-h-20 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] p-3"
          disabled={disabled ?? testing}
          onChange={(event) => setProbeInput(event.target.value)}
          value={probeInput}
        />
      </label>

      {error ? (
        <div className="rounded bg-[var(--danger-bg)] px-3 py-2 text-sm text-[var(--danger)]">
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="space-y-2 rounded bg-[var(--success-bg)] px-3 py-2">
          <div className="flex gap-4 text-xs">
            <span>
              状态码：{" "}
              <span className="font-mono font-semibold">
                {result.status_code}
              </span>
            </span>
            <span>
              延迟：{" "}
              <span className="font-mono font-semibold">
                {result.latency_ms}ms
              </span>
            </span>
          </div>
          <div>
            <span className="text-xs text-[var(--muted)]">响应预览</span>
            <pre className="text-code mt-1 max-h-40 overflow-auto rounded bg-[var(--surface)] p-2">
              {JSON.stringify(result.response_preview, null, 2)}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}
