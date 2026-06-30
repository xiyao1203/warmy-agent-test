"use client";

import {
  AlertTriangle,
  Bug,
  ChevronDown,
  ChevronRight,
  PlayCircle,
  Shield,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import type { Finding, SecurityScanItem } from "./api";
import { listScans, triggerScan } from "./api";

const SEVERITY_TONES: Record<string, "danger" | "warning" | "neutral"> = {
  high: "danger",
  medium: "warning",
  low: "neutral",
};

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  injection: <Bug className="size-4" />,
  leak: <AlertTriangle className="size-4" />,
  jailbreak: <ShieldAlert className="size-4" />,
};

export function SecurityScanPage({ projectId }: { projectId: string }) {
  const [scans, setScans] = useState<SecurityScanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [agentEndpoint, setAgentEndpoint] = useState("");
  const [triggerError, setTriggerError] = useState<string | null>(null);
  const [selectedScan, setSelectedScan] = useState<SecurityScanItem | null>(
    null,
  );

  useEffect(() => {
    let active = true;
    void listScans(projectId)
      .then((items) => {
        if (active) setScans(items);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  async function handleTrigger() {
    if (!agentEndpoint.trim()) {
      setTriggerError("请输入真实 Agent API 地址");
      return;
    }
    setTriggering(true);
    setTriggerError(null);
    try {
      const scan = await triggerScan(projectId, agentEndpoint.trim());
      setScans((prev) => [scan, ...prev]);
      setSelectedScan(scan);
    } catch (error) {
      setTriggerError(
        error instanceof Error ? error.message : "安全扫描启动失败",
      );
    } finally {
      setTriggering(false);
    }
  }

  if (loading) {
    return (
      <div className="grid min-h-[40vh] place-items-center text-sm text-[var(--text-muted)]">
        正在加载安全扫描…
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <Shield className="size-6" />
            安全测试
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Promptfoo 安全扫描：注入、泄露、越狱检测。
          </p>
        </div>
        <div className="flex min-w-80 flex-col items-end gap-2">
          <div className="flex w-full gap-2">
            <Input
              aria-label="Agent API 地址"
              disabled={triggering}
              onChange={(event) => setAgentEndpoint(event.target.value)}
              placeholder="https://agent.example.com/chat"
              type="url"
              value={agentEndpoint}
            />
            <Button
              disabled={triggering || !agentEndpoint.trim()}
              loading={triggering}
              onClick={handleTrigger}
              variant="primary"
            >
              <PlayCircle className="mr-1.5 size-4" />
              触发扫描
            </Button>
          </div>
          {triggerError ? (
            <p className="text-xs text-[var(--error)]">{triggerError}</p>
          ) : null}
        </div>
      </header>

      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_24rem] gap-5 max-[1100px]:grid-cols-1">
        {/* 扫描列表 */}
        <ul className="space-y-2">
          {scans.length === 0 ? (
            <li className="rounded border border-dashed border-[var(--border)] p-10 text-center">
              <ShieldCheck className="mx-auto size-8 text-[var(--text-muted)]" />
              <p className="mt-3 text-sm font-medium text-[var(--text-muted)]">
                暂无扫描记录
              </p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                点击「触发扫描」开始安全检测。
              </p>
            </li>
          ) : (
            scans.map((scan) => (
              <li key={scan.id}>
                <button
                  className={`flex w-full items-center gap-3 rounded border px-4 py-3 text-left text-sm transition-colors ${
                    selectedScan?.id === scan.id
                      ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                      : "border-[var(--border)] hover:bg-[var(--surface-subtle)]"
                  }`}
                  onClick={() => setSelectedScan(scan)}
                  type="button"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-mono text-xs">{scan.id.slice(0, 12)}</p>
                    <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                      {scan.scan_type} ·{" "}
                      {new Date(scan.created_at).toLocaleString("zh-CN")}
                    </p>
                  </div>
                  <Badge
                    tone={
                      scan.status === "completed"
                        ? "success"
                        : scan.status === "failed"
                          ? "danger"
                          : "warning"
                    }
                  >
                    {scan.status}
                  </Badge>
                  {scan.summary.injection != null ||
                  scan.summary.leak != null ||
                  scan.summary.jailbreak != null ? (
                    <span className="text-xs text-[var(--text-muted)]">
                      {Object.entries(scan.summary)
                        .filter(([k]) => k !== "error")
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(" · ")}
                    </span>
                  ) : null}
                  {selectedScan?.id === scan.id ? (
                    <ChevronDown className="size-4" />
                  ) : (
                    <ChevronRight className="size-4 text-[var(--text-muted)]" />
                  )}
                </button>
              </li>
            ))
          )}
        </ul>

        {/* 详情面板 */}
        <aside className="h-fit rounded border border-[var(--border)] bg-[var(--surface)] p-5">
          {selectedScan ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold">扫描详情</h2>
                <Badge
                  tone={
                    selectedScan.status === "completed"
                      ? "success"
                      : selectedScan.status === "failed"
                        ? "danger"
                        : "warning"
                  }
                >
                  {selectedScan.status}
                </Badge>
              </div>

              {/* 统计摘要 */}
              <div className="grid grid-cols-3 gap-2 text-center">
                {(["injection", "leak", "jailbreak"] as const).map((cat) => (
                  <div
                    className="rounded border border-[var(--border)] p-2"
                    key={cat}
                  >
                    <div className="flex items-center justify-center gap-1 text-[var(--text-muted)]">
                      {CATEGORY_ICONS[cat]}
                      <span className="text-xs capitalize">{cat}</span>
                    </div>
                    <p className="mt-1 text-lg font-semibold">
                      {selectedScan.summary[cat] ?? 0}
                    </p>
                  </div>
                ))}
              </div>

              {/* 发现列表 */}
              {selectedScan.findings.length > 0 ? (
                <div className="space-y-2">
                  <h3 className="text-xs font-medium text-[var(--text-muted)]">
                    发现详情（{selectedScan.findings.length} 项）
                  </h3>
                  {selectedScan.findings.map((f, i) => (
                    <FindingCard finding={f} key={i} />
                  ))}
                </div>
              ) : (
                <p className="text-xs text-[var(--text-muted)]">暂无发现</p>
              )}
            </div>
          ) : (
            <div className="py-10 text-center text-sm text-[var(--text-muted)]">
              <Shield className="mx-auto size-8" />
              <p className="mt-2">选择一个扫描查看详情</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function FindingCard({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded border border-[var(--border)]">
      <button
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs"
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <Badge tone={SEVERITY_TONES[finding.severity] ?? "neutral"}>
          {finding.severity}
        </Badge>
        <span className="flex-1 font-medium">{finding.title}</span>
        <Badge>{finding.category}</Badge>
        {expanded ? (
          <ChevronDown className="size-3" />
        ) : (
          <ChevronRight className="size-3" />
        )}
      </button>
      {expanded ? (
        <div className="border-t border-[var(--border)] px-3 py-2 text-xs">
          <p className="text-[var(--text-muted)]">{finding.description}</p>
          <div className="mt-2 grid grid-cols-2 gap-2">
            <div>
              <p className="font-medium text-[var(--text)]">攻击向量</p>
              <p className="mt-0.5 text-[var(--text-muted)]">
                {finding.vector}
              </p>
            </div>
            <div>
              <p className="font-medium text-[var(--text)]">响应</p>
              <p className="mt-0.5 text-[var(--text-muted)]">
                {finding.response}
              </p>
            </div>
          </div>
          <p className="mt-2">
            <span className="font-medium">评分：</span>
            <span
              className={
                finding.score < 0.5
                  ? "text-[var(--danger)]"
                  : finding.score < 0.8
                    ? "text-[var(--warning)]"
                    : "text-[var(--success)]"
              }
            >
              {finding.score.toFixed(2)}
            </span>
          </p>
        </div>
      ) : null}
    </div>
  );
}
