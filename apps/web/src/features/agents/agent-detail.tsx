"use client";

import type {
  AgentResponse,
  AgentVersionResponse,
  CreateAgentVersionRequest,
} from "@warmy/generated-api-client";
import {
  ArrowLeft,
  Bot,
  Clock,
  Cog,
  Download,
  Layers,
  LockKeyhole,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";

import { AgentVersionDialog } from "./agent-version-dialog";

type AgentDetailProps = {
  agent: AgentResponse;
  loading?: boolean;
  onCreateVersion?: (payload: CreateAgentVersionRequest) => Promise<unknown>;
  onPublish?: (versionId: string) => Promise<unknown>;
  onUpdateVersion?: (
    versionId: string,
    payload: CreateAgentVersionRequest,
  ) => Promise<unknown>;
  versions?: AgentVersionResponse[];
};

type TabKey = "overview" | "config" | "versions" | "runs" | "artifacts";

const TABS: { key: TabKey; icon: React.ReactNode; label: string }[] = [
  { key: "overview", icon: <Bot aria-hidden="true" className="size-4" />, label: "概览" },
  { key: "config", icon: <Cog aria-hidden="true" className="size-4" />, label: "配置" },
  { key: "versions", icon: <Layers aria-hidden="true" className="size-4" />, label: "版本历史" },
  { key: "runs", icon: <Clock aria-hidden="true" className="size-4" />, label: "运行记录" },
  { key: "artifacts", icon: <Download aria-hidden="true" className="size-4" />, label: "产物" },
];

export function AgentDetail({
  agent,
  loading = false,
  onCreateVersion = async () => undefined,
  onPublish = async () => undefined,
  onUpdateVersion = async () => undefined,
  versions = [],
}: AgentDetailProps) {
  const [publishVersion, setPublishVersion] = useState<AgentVersionResponse>();
  const [activeTab, setActiveTab] = useState<TabKey>("versions");

  if (loading) return <div className="p-6">正在加载 Agent 详情…</div>;

  const publishedVersions = versions.filter((v) => v.status === "published");
  const latestPublished = publishedVersions[0];

  return (
    <div className="min-w-0 px-6 py-6">
      <Link
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
        href={`/projects/${agent.project_id}/agents`}
      >
        <ArrowLeft aria-hidden="true" className="size-4" />
        返回 Agent 列表
      </Link>

      {/* ── 顶部固定区 ─────────────────────────────────────────────────── */}
      <header className="mt-4 flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{agent.name}</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {agent.description || "暂无描述"}
          </p>
        </div>
        <AgentVersionDialog
          onSubmit={onCreateVersion}
          triggerLabel="创建版本"
        />
      </header>

      {/* ── Tabs ───────────────────────────────────────────────────────── */}
      <nav className="mt-4 flex gap-1 border-b border-[var(--border)]">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex h-10 items-center gap-2 px-4 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "border-b-2 border-[var(--accent)] text-[var(--accent)]"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </nav>

      {/* ── Tab 内容 ───────────────────────────────────────────────────── */}
      <section className="mt-5">
        {activeTab === "overview" && (
          <OverviewTab agent={agent} versions={versions} latestPublished={latestPublished} />
        )}
        {activeTab === "config" && (
          <ConfigTab versions={versions} />
        )}
        {activeTab === "versions" && (
          <VersionsTab
            versions={versions}
            onPublish={onPublish}
            onUpdateVersion={onUpdateVersion}
            setPublishVersion={setPublishVersion}
          />
        )}
        {activeTab === "runs" && <RunsTab />}
        {activeTab === "artifacts" && <ArtifactsTab />}
      </section>

      {/* ── 发布确认对话框 ─────────────────────────────────────────────── */}
      <Dialog
        onOpenChange={(open) => {
          if (!open) setPublishVersion(undefined);
        }}
        open={Boolean(publishVersion)}
      >
        <DialogContent>
          <DialogTitle>发布 Agent 版本</DialogTitle>
          <DialogDescription>发布后该版本将不可编辑。</DialogDescription>
          <div className="mt-5 flex justify-end gap-2">
            <Button onClick={() => setPublishVersion(undefined)}>取消</Button>
            <Button
              onClick={async () => {
                if (!publishVersion) return;
                await onPublish(publishVersion.id);
                setPublishVersion(undefined);
              }}
              variant="primary"
            >
              确认发布
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/* ── Tab 子组件 ──────────────────────────────────────────────────────── */

function OverviewTab({
  agent,
  versions,
  latestPublished,
}: {
  agent: AgentResponse;
  versions: AgentVersionResponse[];
  latestPublished?: AgentVersionResponse;
}) {
  return (
    <div className="space-y-4">
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4">
        <h3 className="text-sm font-semibold">Agent 信息</h3>
        <dl className="mt-3 space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-[var(--text-muted)]">类型</dt>
            <dd className="font-medium">{agent.agent_type === "canvas" ? "画布 Agent" : "通用 HTTP"}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[var(--text-muted)]">版本数</dt>
            <dd className="font-medium">{versions.length}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[var(--text-muted)]">已发布</dt>
            <dd className="font-medium">{versions.filter((v) => v.status === "published").length}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[var(--text-muted)]">草稿</dt>
            <dd className="font-medium">{versions.filter((v) => v.status === "draft").length}</dd>
          </div>
        </dl>
      </div>

      {latestPublished && (
        <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4">
          <h3 className="text-sm font-semibold">当前版本</h3>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            版本 v{latestPublished.version_number} · {String(latestPublished.config.model ?? "未指定模型")} ·
            {" "}{String(latestPublished.config.api_url ?? "未配置 API")}
          </p>
        </div>
      )}
    </div>
  );
}

function ConfigTab({ versions }: { versions: AgentVersionResponse[] }) {
  const current = versions.find((v) => v.status === "published") || versions[0];
  if (!current) {
    return (
      <p className="text-sm text-[var(--text-muted)]">暂无配置，请先创建版本。</p>
    );
  }

  const config = current.config as Record<string, unknown>;
  const fields = [
    { key: "api_url", label: "API 地址" },
    { key: "model", label: "模型" },
    { key: "timeout", label: "超时（秒）" },
    { key: "max_steps", label: "最大步数" },
    { key: "cost_limit", label: "成本限制" },
    { key: "system_prompt_version", label: "Prompt 版本" },
    { key: "knowledge_version", label: "知识库版本" },
    { key: "adapter_version", label: "Adapter 版本" },
  ];

  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4">
      <h3 className="text-sm font-semibold">版本 v{current.version_number} 配置</h3>
      <dl className="mt-3 space-y-2 text-sm">
        {fields.map((f) => (
          <div key={f.key} className="flex justify-between">
            <dt className="text-[var(--text-muted)]">{f.label}</dt>
            <dd className="max-w-60 truncate font-medium">{String(config[f.key] ?? "未设置")}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function VersionsTab({
  versions,
  onUpdateVersion,
  setPublishVersion,
}: {
  versions: AgentVersionResponse[];
  onPublish?: (versionId: string) => Promise<unknown>;
  onUpdateVersion?: (
    versionId: string,
    payload: CreateAgentVersionRequest,
  ) => Promise<unknown>;
  setPublishVersion: (v: AgentVersionResponse) => void;
}) {
  if (!versions.length) {
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-8 text-center">
        <p className="text-sm font-medium">暂无版本</p>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          创建第一个连接配置后即可发布测试。
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {versions.map((version) => (
        <article
          className="flex items-center justify-between gap-4 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
          key={version.id}
        >
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold">版本 v{version.version_number}</h2>
              <Badge tone={version.status === "published" ? "success" : "warning"}>
                {version.status === "published" ? "已发布" : "草稿"}
              </Badge>
              {version.status === "published" && (
                <span className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)]">
                  <LockKeyhole aria-hidden="true" className="size-3.5" />
                  已锁定
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              {String(version.config.api_url ?? "未配置 API 地址")}
            </p>
          </div>
          {version.status === "draft" && (
            <div className="flex gap-2">
              <AgentVersionDialog
                onSubmit={async (payload) => { await onUpdateVersion?.(version.id, payload); }}
                triggerLabel={`编辑 v${version.version_number}`}
                version={version}
              />
              <Button
                aria-label={`发布版本 v${version.version_number}`}
                onClick={() => setPublishVersion(version)}
                variant="primary"
              >
                发布
              </Button>
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

function RunsTab() {
  return (
    <p className="text-sm text-[var(--text-muted)]">
      运行记录需在「测试执行」页面查看。请访问左侧导航的「测试执行」。
    </p>
  );
}

function ArtifactsTab() {
  return (
    <p className="text-sm text-[var(--text-muted)]">
      产物列表需在运行详情页面查看。请先运行测试后在「测试执行」页面查看产物。
    </p>
  );
}
