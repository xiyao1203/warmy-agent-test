"use client";

import type {
  CreateTestPlanVersionRequest,
  TestPlanResponse,
  TestPlanVersionResponse,
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

import {
  TestPlanVersionDialog,
  type VersionAssetOption,
} from "./test-plan-version-dialog";

export function TestPlanDetail({
  agentVersions,
  datasetVersions,
  environments,
  onCreateVersion = async () => undefined,
  onPublish = async () => undefined,
  onUpdateVersion = async () => undefined,
  plan,
  versions = [],
}: {
  agentVersions: VersionAssetOption[];
  datasetVersions: VersionAssetOption[];
  environments: VersionAssetOption[];
  onCreateVersion?: (payload: CreateTestPlanVersionRequest) => Promise<unknown>;
  onPublish?: (versionId: string) => Promise<unknown>;
  onUpdateVersion?: (
    versionId: string,
    payload: CreateTestPlanVersionRequest,
  ) => Promise<unknown>;
  plan: TestPlanResponse;
  versions?: TestPlanVersionResponse[];
}) {
  const [publishVersion, setPublishVersion] =
    useState<TestPlanVersionResponse>();
  return (
    <div className="min-w-0 px-6 py-6">
      <Link
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
        href={`/projects/${plan.project_id}/test-plans`}
      >
        <ArrowLeft aria-hidden="true" className="size-4" />
        返回测试计划列表
      </Link>
      <header className="mt-4 flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{plan.name}</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {plan.description || "暂无描述"}
          </p>
        </div>
        <TestPlanVersionDialog
          agentVersions={agentVersions}
          datasetVersions={datasetVersions}
          environments={environments}
          onSubmit={onCreateVersion}
          triggerLabel="创建版本"
        />
      </header>
      <section className="mt-5 space-y-3">
        {versions.map((version) => (
          <article
            className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-4 py-4"
            key={version.id}
          >
            <div className="flex items-center justify-between gap-4">
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
                <p className="mt-2 text-xs text-[var(--text-muted)]">
                  并发 {String(version.config.concurrency ?? 1)} · 超时{" "}
                  {String(version.config.timeout ?? 300)} 秒 · 每用例{" "}
                  {String(version.config.runs_per_case ?? 1)} 次 · 阈值{" "}
                  {String(version.config.pass_threshold ?? 1)}
                </p>
              </div>
              {version.status === "draft" ? (
                <div className="flex gap-2">
                  <TestPlanVersionDialog
                    agentVersions={agentVersions}
                    datasetVersions={datasetVersions}
                    environments={environments}
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
            </div>
          </article>
        ))}
      </section>
      <Dialog
        onOpenChange={(open) => {
          if (!open) setPublishVersion(undefined);
        }}
        open={Boolean(publishVersion)}
      >
        <DialogContent>
          <DialogTitle>发布测试计划版本</DialogTitle>
          <DialogDescription>发布后计划版本将不可编辑。</DialogDescription>
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
