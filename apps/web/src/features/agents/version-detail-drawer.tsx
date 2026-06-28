"use client";

import type { AgentVersionResponse } from "@warmy/generated-api-client";
import { Layers, LockKeyhole, GitBranch, Clock, Cpu, Wrench } from "lucide-react";

import { Badge } from "@/components/ui/badge";

type VersionDetailDrawerProps = {
  version: AgentVersionResponse;
  isCurrent?: boolean;
  isBaseline?: boolean;
  open: boolean;
  onClose: () => void;
};

export function VersionDetailDrawer({
  version,
  isCurrent = false,
  isBaseline = false,
  open,
  onClose,
}: VersionDetailDrawerProps) {
  if (!open) return null;

  const config = version.config as Record<string, unknown>;
  const modelParams = config.model_params as Record<string, unknown> | undefined;
  const tools = config.tools as Array<Record<string, string>> | undefined;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* 遮罩 */}
      <div
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
        role="button"
        tabIndex={0}
        aria-label="关闭"
      />

      {/* 抽屉内容 */}
      <div className="relative z-10 w-full max-w-md overflow-y-auto border-l border-[var(--border)] bg-[var(--surface)] p-6 shadow-xl">
        {/* 头部 */}
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
          <div>
            <h2 className="text-lg font-semibold">版本 v{version.version_number} 详情</h2>
            <div className="mt-2 flex gap-2">
              <Badge tone={version.status === "published" ? "success" : "warning"}>
                {version.status === "published" ? "已发布" : "草稿"}
              </Badge>
              {isCurrent && <Badge tone="accent">当前版本</Badge>}
              {isBaseline && <Badge tone="neutral">基线版本</Badge>}
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-[var(--surface-subtle)]"
            aria-label="关闭"
          >
            <svg className="size-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* 基本信息 */}
        <div className="mt-6 space-y-6">
          <Section title="基本信息" icon={<Layers className="size-4" />}>
            <Field label="版本 ID" value={version.id} />
            <Field label="版本号" value={`v${version.version_number}`} />
            <Field
              label="状态"
              value={version.status === "published" ? "已发布（不可修改）" : "草稿（可编辑）"}
            />
            {version.published_at && (
              <Field label="发布时间" value={formatDate(version.published_at)} />
            )}
            <Field label="创建时间" value={formatDate(version.created_at)} />
            <Field label="更新时间" value={formatDate(version.updated_at)} />
          </Section>

          {/* Agent 配置 */}
          <Section title="Agent 配置" icon={<Cpu className="size-4" />}>
            <Field label="API 地址" value={String(config.api_url ?? "未设置")} />
            <Field label="模型" value={String(config.model ?? "未指定")} />
            <Field label="代码版本" value={String(config.code_version ?? "未设置")} />
            <Field label="Git Commit" value={String(config.git_commit ?? "未设置")} monospace />
          </Section>

          {/* 模型参数 */}
          {modelParams && Object.keys(modelParams).length > 0 && (
            <Section title="模型参数" icon={<Cpu className="size-4" />}>
              <JsonBlock data={modelParams} />
            </Section>
          )}

          {/* Prompt 与知识库 */}
          <Section title="Prompt 与知识库" icon={<GitBranch className="size-4" />}>
            <Field label="System Prompt 版本" value={String(config.system_prompt_version ?? "未设置")} />
            <Field label="知识库版本" value={String(config.knowledge_version ?? "未设置")} />
            <Field label="Adapter 版本" value={String(config.adapter_version ?? "未设置")} />
            {String(config.system_prompt ?? "") && (
              <Field label="System Prompt" value={String(config.system_prompt)} multiline />
            )}
          </Section>

          {/* 执行限制 */}
          <Section title="执行限制" icon={<Clock className="size-4" />}>
            <Field label="超时（秒）" value={String(config.timeout ?? 30)} />
            <Field label="最大步数" value={config.max_steps ? String(config.max_steps) : "无限制"} />
            <Field label="成本限制" value={config.cost_limit ? `¥${config.cost_limit}` : "无限制"} />
          </Section>

          {/* 工具清单 */}
          {tools && tools.length > 0 && (
            <Section title="工具清单" icon={<Wrench className="size-4" />}>
              <div className="space-y-2">
                {tools.map((tool, i) => (
                  <div
                    key={i}
                    className="rounded border border-[var(--border)] bg-[var(--surface-subtle)] p-2 text-xs"
                  >
                    <span className="font-medium">{tool.name || `工具 ${i + 1}`}</span>
                    {tool.description && (
                      <p className="mt-1 text-[var(--text-muted)]">{tool.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── 子组件 ────────────────────────────────────────────────────────── */

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text)]">
        {icon}
        {title}
      </div>
      <div className="mt-3 space-y-2 text-sm">{children}</div>
    </div>
  );
}

function Field({
  label,
  value,
  monospace = false,
  multiline = false,
}: {
  label: string;
  value: string | number | null | undefined;
  monospace?: boolean;
  multiline?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
      <dt className="text-[var(--text-muted)]">{label}</dt>
      <dd
        className={`max-w-60 ${monospace ? "font-mono text-xs" : ""} ${
          multiline ? "whitespace-pre-wrap" : "truncate"
        } font-medium`}
      >
        {value == null ? "—" : String(value)}
      </dd>
    </div>
  );
}

function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre className="max-h-40 overflow-auto rounded border border-[var(--border)] bg-[var(--surface-subtle)] p-3 text-xs font-mono">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleString("zh-CN");
  } catch {
    return dateStr;
  }
}
