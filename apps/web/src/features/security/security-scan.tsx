"use client";

import {
  AlertTriangle,
  Bug,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  PlayCircle,
  Shield,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import { ResourceReferenceLink } from "@/components/ui/resource-reference-link";
import type { Finding, SecurityScanItem } from "./api";
import type { SecurityTarget } from "./api";
import { listScans, listSecurityTargets, triggerScan } from "./api";

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

const CATEGORY_LABELS: Record<string, string> = {
  injection: "注入",
  jailbreak: "越狱",
  leak: "泄露",
};

export function SecurityScanPage({ projectId }: { projectId: string }) {
  const [scans, setScans] = useState<SecurityScanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [agentVersionId, setAgentVersionId] = useState("");
  const [targets, setTargets] = useState<SecurityTarget[]>([]);
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

  useEffect(() => {
    void listSecurityTargets(projectId)
      .then(setTargets)
      .catch(() => setTargets([]));
  }, [projectId]);

  async function handleTrigger() {
    if (!agentVersionId) {
      setTriggerError("请选择已发布的 Agent 版本");
      return;
    }
    setTriggering(true);
    setTriggerError(null);
    try {
      const scan = await triggerScan(projectId, agentVersionId);
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
      <div className="grid min-h-[40vh] place-items-center text-sm text-[var(--muted)]">
        正在加载安全扫描…
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <Shield className="size-6" />
            安全测试
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            对已发布 Agent 做注入、泄露、越狱检测；结果会进入发布门禁评估。
          </p>
        </div>
        <div className="flex min-w-80 flex-col items-end gap-2">
          <div className="flex w-full gap-2">
            <DropdownSelect
              aria-label="已发布 Agent 版本"
              className="h-9 min-w-64 rounded border border-[var(--hairline)] bg-[var(--surface)] px-3 text-sm"
              disabled={triggering}
              onChange={(event) => setAgentVersionId(event.target.value)}
              value={agentVersionId}
            >
              <option value="">选择已发布 Agent 版本</option>
              {targets.map((target) => (
                <option key={target.id} value={target.id}>
                  {target.label}
                </option>
              ))}
            </DropdownSelect>
            <Button
              disabled={triggering || !agentVersionId}
              loading={triggering}
              onClick={handleTrigger}
              variant="primary"
            >
              <PlayCircle className="mr-1.5 size-4" />
              启动安全测试
            </Button>
          </div>
          {triggerError ? (
            <p className="text-xs text-[var(--danger)]">{triggerError}</p>
          ) : null}
        </div>
      </header>

      <section className="mt-5 grid gap-3 md:grid-cols-4">
        <FlowCard
          description="先发布可测版本"
          href={`/projects/${projectId}/agents`}
          icon={<Shield aria-hidden="true" className="size-4" />}
          label="1. 选择 Agent 版本"
        />
        <FlowCard
          description="自动执行风险探测"
          icon={<PlayCircle aria-hidden="true" className="size-4" />}
          label="2. 启动安全测试"
        />
        <FlowCard
          description="确认注入、泄露、越狱"
          href={`/projects/${projectId}/runs`}
          icon={<ClipboardCheck aria-hidden="true" className="size-4" />}
          label="3. 查看运行证据"
        />
        <FlowCard
          description="安全评分参与放行"
          href={`/projects/${projectId}/gates`}
          icon={<ShieldCheck aria-hidden="true" className="size-4" />}
          label="4. 发布门禁判断"
        />
      </section>

      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_24rem] gap-5 max-[1100px]:grid-cols-1">
        {/* 扫描列表 */}
        <ul className="space-y-2">
          {scans.length === 0 ? (
            <li className="rounded border border-dashed border-[var(--hairline)] p-10 text-center">
              <ShieldCheck className="mx-auto size-8 text-[var(--muted)]" />
              <p className="mt-3 text-sm font-medium text-[var(--muted)]">
                暂无扫描记录
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                先选择已发布 Agent
                版本并启动安全测试，完成后安全评分会被发布门禁读取。
              </p>
              <div className="mt-4 flex justify-center gap-3 text-sm">
                <Link
                  className="font-medium text-[var(--primary)] hover:underline"
                  href={`/projects/${projectId}/agents`}
                >
                  去发布 Agent
                </Link>
                <Link
                  className="font-medium text-[var(--primary)] hover:underline"
                  href={`/projects/${projectId}/gates`}
                >
                  配置发布门禁
                </Link>
              </div>
            </li>
          ) : (
            scans.map((scan) => (
              <li key={scan.id}>
                <button
                  className={`flex w-full items-center gap-3 rounded border px-4 py-3 text-left text-sm transition-colors ${
                    selectedScan?.id === scan.id
                      ? "border-[var(--primary)] bg-[var(--primary-subtle)]"
                      : "border-[var(--hairline)] hover:bg-[var(--canvas-soft)]"
                  }`}
                  onClick={() => setSelectedScan(scan)}
                  type="button"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-mono text-xs">{scan.id.slice(0, 12)}</p>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      {scan.scan_type} ·{" "}
                      {new Date(scan.created_at).toLocaleString("zh-CN")}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      Agent {scan.agent_ref?.name ?? "暂无数据"} · 运行{" "}
                      {scan.run_ref?.name ?? "暂无数据"} · 配置{" "}
                      {scan.profile_ref?.name ?? "暂无数据"}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      严重 {scan.critical_count ?? 0} · 高{" "}
                      {scan.high_count ?? 0} · 中 {scan.medium_count ?? 0} · 低{" "}
                      {scan.low_count ?? 0} · 耗时{" "}
                      {scan.duration_ms == null
                        ? "暂无数据"
                        : `${scan.duration_ms} ms`}
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
                    <span className="text-xs text-[var(--muted)]">
                      {Object.entries(scan.summary)
                        .filter(([k]) => k !== "error")
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(" · ")}
                    </span>
                  ) : null}
                  {selectedScan?.id === scan.id ? (
                    <ChevronDown className="size-4" />
                  ) : (
                    <ChevronRight className="size-4 text-[var(--muted)]" />
                  )}
                </button>
              </li>
            ))
          )}
        </ul>

        {/* 详情面板 */}
        <aside className="h-fit rounded border border-[var(--hairline)] bg-[var(--surface)] p-5">
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

              <div className="grid gap-2 text-xs text-[var(--muted)]">
                <p>
                  Agent：
                  <ResourceReferenceLink reference={selectedScan.agent_ref} />
                </p>
                <p>
                  运行：
                  <ResourceReferenceLink reference={selectedScan.run_ref} />
                </p>
                <p>
                  安全配置：
                  <ResourceReferenceLink reference={selectedScan.profile_ref} />
                </p>
                <p>
                  开始时间{" "}
                  {selectedScan.started_at
                    ? new Date(selectedScan.started_at).toLocaleString("zh-CN")
                    : "暂无数据"}{" "}
                  · 耗时{" "}
                  {selectedScan.duration_ms == null
                    ? "暂无数据"
                    : `${selectedScan.duration_ms} ms`}
                </p>
              </div>

              {/* 统计摘要 */}
              <div className="grid grid-cols-3 gap-2 text-center">
                {(["injection", "leak", "jailbreak"] as const).map((cat) => (
                  <div
                    className="rounded border border-[var(--hairline)] p-2"
                    key={cat}
                  >
                    <div className="flex items-center justify-center gap-1 text-[var(--muted)]">
                      {CATEGORY_ICONS[cat]}
                      <span className="text-xs">{CATEGORY_LABELS[cat]}</span>
                    </div>
                    <p className="mt-1 text-lg font-semibold">
                      {selectedScan.summary[cat] ?? 0}
                    </p>
                  </div>
                ))}
              </div>

              <div className="rounded border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3 text-xs leading-5 text-[var(--muted)]">
                安全发现会作为同一次运行的门禁证据。高风险项建议先修复或进入人工审核，再重新运行门禁评估。
                <div className="mt-2 flex flex-wrap gap-3">
                  <Link
                    className="font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/gates`}
                  >
                    查看发布门禁
                  </Link>
                  <Link
                    className="font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/reviews`}
                  >
                    去人工审核
                  </Link>
                  <Link
                    className="font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/test-plans`}
                  >
                    调整测试计划
                  </Link>
                </div>
              </div>

              {/* 发现列表 */}
              {selectedScan.findings.length > 0 ? (
                <div className="space-y-2">
                  <h3 className="text-xs font-medium text-[var(--muted)]">
                    发现详情（{selectedScan.findings.length} 项）
                  </h3>
                  {selectedScan.findings.map((f, i) => (
                    <FindingCard finding={f} key={i} />
                  ))}
                </div>
              ) : (
                <p className="text-xs text-[var(--muted)]">暂无发现</p>
              )}
            </div>
          ) : (
            <div className="py-10 text-center text-sm text-[var(--muted)]">
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
    <div className="rounded border border-[var(--hairline)]">
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
        <div className="border-t border-[var(--hairline)] px-3 py-2 text-xs">
          <p className="text-[var(--muted)]">{finding.description}</p>
          <div className="mt-2 grid grid-cols-2 gap-2">
            <div>
              <p className="font-medium text-[var(--ink)]">攻击向量</p>
              <p className="mt-0.5 text-[var(--muted)]">{finding.vector}</p>
            </div>
            <div>
              <p className="font-medium text-[var(--ink)]">响应</p>
              <p className="mt-0.5 text-[var(--muted)]">{finding.response}</p>
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

function FlowCard({
  description,
  href,
  icon,
  label,
}: {
  description: string;
  href?: string;
  icon: ReactNode;
  label: string;
}) {
  const content = (
    <>
      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)]">
        {icon}
      </span>
      <span className="min-w-0">
        <span className="block font-medium">{label}</span>
        <span className="block truncate text-xs text-[var(--muted)]">
          {description}
        </span>
      </span>
    </>
  );

  if (href) {
    return (
      <Link
        className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm transition-colors hover:border-[var(--primary)]"
        href={href}
      >
        {content}
      </Link>
    );
  }

  return (
    <div className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm">
      {content}
    </div>
  );
}
