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
  GitBranch,
  Pencil,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/uiverse";

import { AgentVersionDialog } from "./agent-version-dialog";
import { ArtifactsTab, RelationshipsTab, RunsTab } from "./agent-detail-tabs";
import { VersionDetailDrawer } from "./version-detail-drawer";
import { VersionDiffView } from "./version-diff-view";
import type { AgentRelationships } from "./api";

type AgentDetailProps = {
  agent: AgentResponse;
  loading?: boolean;
  onCreateVersion?: (payload: CreateAgentVersionRequest) => Promise<void>;
  onPublish?: (versionId: string) => Promise<unknown>;
  onUpdateVersion?: (
    versionId: string,
    payload: CreateAgentVersionRequest,
  ) => Promise<void>;
  onSetCurrentVersion?: (versionId: string) => Promise<unknown>;
  onSetBaselineVersion?: (versionId: string) => Promise<unknown>;
  onFetchDiff?: (v1Id: string, v2Id: string) => Promise<unknown>;
  versions?: AgentVersionResponse[];
  relationships?: AgentRelationships;
  onUpdateAgent?: (payload: {
    name?: string;
    description?: string | null;
  }) => Promise<void>;
};

type TabKey =
  | "overview"
  | "config"
  | "versions"
  | "runs"
  | "artifacts"
  | "relationships";

const TABS: { key: TabKey; icon: React.ReactNode; label: string }[] = [
  {
    key: "overview",
    icon: <Bot aria-hidden="true" className="size-4" />,
    label: "概览",
  },
  {
    key: "config",
    icon: <Cog aria-hidden="true" className="size-4" />,
    label: "配置",
  },
  {
    key: "versions",
    icon: <Layers aria-hidden="true" className="size-4" />,
    label: "版本历史",
  },
  {
    key: "runs",
    icon: <Clock aria-hidden="true" className="size-4" />,
    label: "运行记录",
  },
  {
    key: "artifacts",
    icon: <Download aria-hidden="true" className="size-4" />,
    label: "产物",
  },
  {
    key: "relationships",
    icon: <GitBranch aria-hidden="true" className="size-4" />,
    label: "关联资产",
  },
];

export function AgentDetail({
  agent,
  loading = false,
  onCreateVersion = async () => undefined,
  onPublish = async () => undefined,
  onUpdateVersion = async () => undefined,
  onSetCurrentVersion = async () => undefined,
  onSetBaselineVersion = async () => undefined,
  onFetchDiff,
  versions = [],
  relationships,
  onUpdateAgent,
}: AgentDetailProps) {
  const [publishVersion, setPublishVersion] = useState<AgentVersionResponse>();
  const [publishing, setPublishing] = useState(false);
  const [selectedVersion, setSelectedVersion] =
    useState<AgentVersionResponse | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [editingAgent, setEditingAgent] = useState(false);
  const [agentName, setAgentName] = useState(agent.name);
  const [agentDescription, setAgentDescription] = useState(
    agent.description ?? "",
  );

  if (loading) {
    return (
      <div className="workspace-page">
        <Skeleton className="mb-2 h-8 w-48" />
        <Skeleton className="mb-6 h-4 w-64" />
        <div className="flex gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-9 w-24" />
          ))}
        </div>
        <Skeleton className="mt-5 h-64 rounded-[var(--radius-lg)]" />
      </div>
    );
  }

  const publishedVersions = versions.filter((v) => v.status === "published");
  const latestPublished = publishedVersions[0];

  return (
    <div className="workspace-page">
      <Link
        className="inline-flex items-center gap-1.5 text-sm text-[var(--muted)] hover:text-[var(--ink)]"
        href={`/projects/${agent.project_id}/agents`}
      >
        <ArrowLeft aria-hidden="true" className="size-4" />
        返回 Agent 列表
      </Link>

      {/* ── 顶部固定区 ─────────────────────────────────────────────────── */}
      <header className="mt-4 flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-page-title">{agent.name}</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {agent.description || "暂无描述"}
          </p>
        </div>
        <div className="flex gap-2">
          {onUpdateAgent ? (
            <Button onClick={() => setEditingAgent(true)} variant="secondary">
              <Pencil className="mr-1 size-4" />
              编辑信息
            </Button>
          ) : null}
          <AgentVersionDialog
            agentId={agent.id}
            onSubmit={onCreateVersion}
            projectId={agent.project_id}
            triggerLabel="创建版本"
          />
        </div>
      </header>

      {/* ── Tabs ───────────────────────────────────────────────────────── */}
      <nav className="mt-4 flex gap-1 border-b border-[var(--hairline)]">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex h-10 items-center gap-2 px-4 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "border-b-2 border-[var(--primary)] text-[var(--primary)]"
                : "text-[var(--muted)] hover:text-[var(--ink)]"
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
          <OverviewTab
            agent={agent}
            versions={versions}
            latestPublished={latestPublished}
            relationships={relationships}
          />
        )}
        {activeTab === "config" && <ConfigTab versions={versions} />}
        {activeTab === "versions" && (
          <VersionsTab
            agentId={agent.id}
            versions={versions}
            currentVersionId={agent.current_version_id ?? undefined}
            baselineVersionId={agent.baseline_version_id ?? undefined}
            onPublish={onPublish}
            onUpdateVersion={onUpdateVersion}
            onSetCurrentVersion={onSetCurrentVersion}
            onSetBaselineVersion={onSetBaselineVersion}
            setPublishVersion={setPublishVersion}
            onViewDetail={setSelectedVersion}
            onFetchDiff={onFetchDiff}
            projectId={agent.project_id}
          />
        )}
        {activeTab === "runs" && (
          <RunsTab
            items={relationships?.runs ?? []}
            projectId={agent.project_id}
          />
        )}
        {activeTab === "artifacts" && (
          <ArtifactsTab
            items={relationships?.artifacts ?? []}
            projectId={agent.project_id}
          />
        )}
        {activeTab === "relationships" && (
          <RelationshipsTab
            relationships={relationships}
            projectId={agent.project_id}
          />
        )}
      </section>

      <Dialog open={editingAgent} onOpenChange={setEditingAgent}>
        <DialogContent>
          <DialogTitle>编辑 Agent 信息</DialogTitle>
          <DialogDescription>
            名称和描述属于稳定 Agent 身份，不修改已发布版本。
          </DialogDescription>
          <div className="mt-4 space-y-3">
            <label className="block text-sm font-medium">
              Agent 名称
              <Input
                className="mt-1"
                value={agentName}
                onChange={(event) => setAgentName(event.target.value)}
              />
            </label>
            <label className="block text-sm font-medium">
              描述
              <Input
                className="mt-1"
                value={agentDescription}
                onChange={(event) => setAgentDescription(event.target.value)}
              />
            </label>
            <div className="flex justify-end gap-2">
              <Button onClick={() => setEditingAgent(false)}>取消</Button>
              <Button
                variant="primary"
                onClick={async () => {
                  await onUpdateAgent?.({
                    name: agentName.trim(),
                    description: agentDescription.trim() || null,
                  });
                  setEditingAgent(false);
                }}
              >
                保存
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

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
            <Button
              disabled={publishing}
              onClick={() => setPublishVersion(undefined)}
            >
              取消
            </Button>
            <Button
              disabled={publishing}
              loading={publishing}
              onClick={async () => {
                if (!publishVersion) return;
                setPublishing(true);
                try {
                  await onPublish(publishVersion.id);
                  setPublishVersion(undefined);
                } finally {
                  setPublishing(false);
                }
              }}
              variant="primary"
            >
              确认发布
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* ── 版本详情抽屉 ─────────────────────────────────────────────── */}
      {selectedVersion && (
        <VersionDetailDrawer
          agentId={agent.id}
          version={selectedVersion}
          isCurrent={selectedVersion.id === agent.current_version_id}
          isBaseline={selectedVersion.id === agent.baseline_version_id}
          open={true}
          onClose={() => setSelectedVersion(null)}
          projectId={agent.project_id}
        />
      )}
    </div>
  );
}

/* ── Tab 子组件 ──────────────────────────────────────────────────────── */

function OverviewTab({
  agent,
  versions,
  latestPublished,
  relationships,
}: {
  agent: AgentResponse;
  versions: AgentVersionResponse[];
  latestPublished?: AgentVersionResponse;
  relationships?: AgentRelationships;
}) {
  if (!versions.length) {
    return (
      <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-6">
        <h2 className="font-semibold">完成 Agent 接入</h2>
        <ol className="mt-4 grid gap-3 text-sm text-[var(--muted)]">
          <li>1. 创建连接版本并填写调用协议</li>
          <li>2. 保存草稿后运行连接测试</li>
          <li>3. 发布通过验证的版本</li>
          <li>4. 将发布版本设为当前版本</li>
        </ol>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-4">
        <h3 className="text-sm font-semibold">Agent 信息</h3>
        <dl className="mt-3 space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-[var(--muted)]">类型</dt>
            <dd className="font-medium">
              {agent.agent_type === "canvas" ? "画布 Agent" : "通用 HTTP"}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[var(--muted)]">版本数</dt>
            <dd className="font-medium">{versions.length}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[var(--muted)]">已发布</dt>
            <dd className="font-medium">
              {versions.filter((v) => v.status === "published").length}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[var(--muted)]">草稿</dt>
            <dd className="font-medium">
              {versions.filter((v) => v.status === "draft").length}
            </dd>
          </div>
        </dl>
      </div>

      {latestPublished && (
        <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-4">
          <h3 className="text-sm font-semibold">当前版本</h3>
          <p className="mt-2 text-sm text-[var(--muted)]">
            版本 v{latestPublished.version_number} ·{" "}
            {String(latestPublished.config.model ?? "未指定模型")} ·{" "}
            {String(latestPublished.config.api_url ?? "未配置 API")}
          </p>
        </div>
      )}
      {relationships ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {[
            ["测试计划", relationships.plans.length],
            ["运行", relationships.runs.length],
            ["产物", relationships.artifacts.length],
            ["实验", relationships.experiments.length],
            ["安全扫描", relationships.security_scans.length],
            ["门禁", relationships.gates.length],
          ].map(([label, count]) => (
            <div
              className="rounded-lg border border-[var(--hairline)] p-3"
              key={String(label)}
            >
              <p className="text-xs text-[var(--muted)]">{label}</p>
              <p className="mt-1 text-xl font-semibold">{count}</p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function ConfigTab({ versions }: { versions: AgentVersionResponse[] }) {
  const current = versions.find((v) => v.status === "published") || versions[0];
  if (!current) {
    return (
      <p className="text-sm text-[var(--muted)]">暂无配置，请先创建版本。</p>
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
    <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-4">
      <h3 className="text-sm font-semibold">
        版本 v{current.version_number} 配置
      </h3>
      <dl className="mt-3 space-y-2 text-sm">
        {fields.map((f) => (
          <div key={f.key} className="flex justify-between">
            <dt className="text-[var(--muted)]">{f.label}</dt>
            <dd className="max-w-60 truncate font-medium">
              {String(config[f.key] ?? "未设置")}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function VersionsTab({
  versions,
  currentVersionId,
  baselineVersionId,
  onUpdateVersion,
  onSetCurrentVersion,
  onSetBaselineVersion,
  setPublishVersion,
  onViewDetail,
  onFetchDiff,
  agentId,
  projectId,
}: {
  versions: AgentVersionResponse[];
  currentVersionId?: string;
  baselineVersionId?: string;
  onPublish?: (versionId: string) => Promise<unknown>;
  onUpdateVersion?: (
    versionId: string,
    payload: CreateAgentVersionRequest,
  ) => Promise<unknown>;
  onSetCurrentVersion?: (versionId: string) => Promise<unknown>;
  onSetBaselineVersion?: (versionId: string) => Promise<unknown>;
  setPublishVersion: (v: AgentVersionResponse) => void;
  onViewDetail: (v: AgentVersionResponse) => void;
  onFetchDiff?: (v1Id: string, v2Id: string) => Promise<unknown>;
  agentId: string;
  projectId: string;
}) {
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);

  function toggleSelect(id: string) {
    setSelectedVersions((prev) =>
      prev.includes(id)
        ? prev.filter((v) => v !== id)
        : prev.length < 2
          ? [...prev, id]
          : prev,
    );
  }

  if (!versions.length) {
    return (
      <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-8 text-center">
        <p className="text-sm font-medium">暂无版本</p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          创建第一个连接配置后即可发布测试。
        </p>
      </div>
    );
  }

  const v1 = versions.find((v) => v.id === selectedVersions[0]);
  const v2 = versions.find((v) => v.id === selectedVersions[1]);

  return (
    <div className="space-y-4">
      {/* 操作栏 */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--muted)]">
          共 {versions.length} 个版本
          {currentVersionId && " · 当前版本已标记"}
          {baselineVersionId && " · 基线版本已标记"}
        </p>
        {selectedVersions.length === 2 && onFetchDiff && (
          <Button
            onClick={() => {
              /* 对比逻辑在下方 VersionDiffView 中 */
            }}
            variant="secondary"
          >
            对比选中版本
          </Button>
        )}
      </div>

      {/* 版本列表 */}
      <div className="space-y-3">
        {versions.map((version) => {
          const isCurrent = version.id === currentVersionId;
          const isBaseline = version.id === baselineVersionId;
          const isSelected = selectedVersions.includes(version.id);

          return (
            <article
              className={`flex items-center justify-between gap-4 rounded-[var(--radius-lg)] border bg-[var(--surface)] px-4 py-3 transition-colors ${
                isSelected
                  ? "border-[var(--primary)] ring-1 ring-[var(--primary)]"
                  : "border-[var(--hairline)]"
              }`}
              key={version.id}
            >
              <div className="flex items-center gap-3">
                {/* 选择框 */}
                <input
                  checked={isSelected}
                  onChange={() => toggleSelect(version.id)}
                  type="checkbox"
                  className="rounded"
                  aria-label="选择版本"
                />

                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-semibold">
                      版本 v{version.version_number}
                    </h2>
                    <Badge
                      tone={
                        version.status === "published" ? "success" : "warning"
                      }
                    >
                      {version.status === "published" ? "已发布" : "草稿"}
                    </Badge>
                    {isCurrent && (
                      <Badge tone="accent">
                        <GitBranch className="mr-1 size-3" />
                        当前
                      </Badge>
                    )}
                    {isBaseline && (
                      <Badge tone="neutral">
                        <GitBranch className="mr-1 size-3" />
                        基线
                      </Badge>
                    )}
                    {version.status === "published" && (
                      <span className="inline-flex items-center gap-1 text-xs text-[var(--muted)]">
                        <LockKeyhole aria-hidden="true" className="size-3.5" />
                        已锁定
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {String(version.config.api_url ?? "未配置 API 地址")}
                  </p>
                </div>
              </div>

              <div className="flex gap-2">
                {/* 查看详情 */}
                <Button
                  onClick={() => onViewDetail(version)}
                  variant="secondary"
                >
                  详情
                </Button>

                {/* 设置当前版本 */}
                {version.status === "published" && !isCurrent && (
                  <Button
                    onClick={() => onSetCurrentVersion?.(version.id)}
                    variant="secondary"
                  >
                    设为当前
                  </Button>
                )}

                {/* 设置基线版本 */}
                {version.status === "published" && !isBaseline && (
                  <Button
                    onClick={() => onSetBaselineVersion?.(version.id)}
                    variant="secondary"
                  >
                    设为基线
                  </Button>
                )}

                {/* 编辑草稿 */}
                {version.status === "draft" && (
                  <>
                    <AgentVersionDialog
                      agentId={agentId}
                      onSubmit={async (payload) => {
                        await onUpdateVersion?.(version.id, payload);
                      }}
                      projectId={projectId}
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
                  </>
                )}
              </div>
            </article>
          );
        })}
      </div>

      {/* 版本对比视图 */}
      {selectedVersions.length === 2 && v1 && v2 && onFetchDiff && (
        <div className="mt-6">
          <VersionDiffView
            v1Id={v1.id}
            v2Id={v2.id}
            v1Number={v1.version_number}
            v2Number={v2.version_number}
            onFetchDiff={
              onFetchDiff as (
                v1Id: string,
                v2Id: string,
              ) => Promise<import("./version-diff-view").VersionDiffResponse>
            }
          />
        </div>
      )}
    </div>
  );
}
