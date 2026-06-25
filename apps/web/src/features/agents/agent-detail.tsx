"use client";

import type {
  AgentResponse,
  AgentVersionResponse,
  CreateAgentVersionRequest,
} from "@warmy/generated-api-client";
import { ArrowLeft, LockKeyhole } from "lucide-react";
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

export function AgentDetail({
  agent,
  loading = false,
  onCreateVersion = async () => undefined,
  onPublish = async () => undefined,
  onUpdateVersion = async () => undefined,
  versions = [],
}: AgentDetailProps) {
  const [publishVersion, setPublishVersion] = useState<AgentVersionResponse>();
  if (loading) return <div className="p-6">正在加载 Agent 详情…</div>;

  return (
    <div className="min-w-0 px-6 py-6">
      <Link
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
        href={`/projects/${agent.project_id}/agents`}
      >
        <ArrowLeft aria-hidden="true" className="size-4" />
        返回 Agent 列表
      </Link>
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
      <section className="mt-5 space-y-3">
        {!versions.length ? (
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-8 text-center">
            <p className="text-sm font-medium">暂无版本</p>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              创建第一个连接配置后即可发布测试。
            </p>
          </div>
        ) : (
          versions.map((version) => (
            <article
              className="flex items-center justify-between gap-4 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
              key={version.id}
            >
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold">
                    版本 v{version.version_number}
                  </h2>
                  <Badge tone={version.status === "published" ? "success" : "warning"}>
                    {version.status === "published" ? "已发布" : "草稿"}
                  </Badge>
                  {version.status === "published" ? (
                    <span className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)]">
                      <LockKeyhole aria-hidden="true" className="size-3.5" />
                      已锁定
                    </span>
                  ) : null}
                </div>
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  {String(version.config.api_url ?? "未配置 API 地址")}
                </p>
              </div>
              {version.status === "draft" ? (
                <div className="flex gap-2">
                  <AgentVersionDialog
                    onSubmit={(payload) => onUpdateVersion(version.id, payload)}
                    triggerLabel={`编辑版本 v${version.version_number}`}
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
              ) : null}
            </article>
          ))
        )}
      </section>
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
