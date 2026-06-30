"use client";

import type {
  CreateTestPlanVersionRequest,
  TestPlanResponse,
  TestPlanVersionResponse,
} from "@warmy/generated-api-client";
import { ArrowLeft, LockKeyhole, PlayCircle } from "lucide-react";
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
import { Tooltip } from "@/components/uiverse";

import { dryRunTestPlanVersion } from "./api";
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
  const [publishing, setPublishing] = useState(false);
  const [dryRunResult, setDryRunResult] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [dryRunLoading, setDryRunLoading] = useState(false);

  async function handleDryRun(versionId: string) {
    setDryRunLoading(true);
    try {
      const result = await dryRunTestPlanVersion(
        plan.project_id,
        plan.id,
        versionId,
      );
      setDryRunResult(result);
    } catch {
      setDryRunResult({ error: "试运行失败" });
    } finally {
      setDryRunLoading(false);
    }
  }
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
                  <Badge
                    tone={
                      version.status === "published" ? "success" : "warning"
                    }
                  >
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
                  {(version.config as Record<string, unknown>).max_retries !=
                    null &&
                  Number(
                    (version.config as Record<string, unknown>).max_retries,
                  ) > 0
                    ? ` · 重试 ${String((version.config as Record<string, unknown>).max_retries)} 次`
                    : ""}
                </p>
              </div>
              {version.status === "draft" ? (
                <div className="flex gap-2">
                  <Tooltip content="编辑此草稿版本的配置">
                    <TestPlanVersionDialog
                      agentVersions={agentVersions}
                      datasetVersions={datasetVersions}
                      environments={environments}
                      onSubmit={(payload) =>
                        onUpdateVersion(version.id, payload)
                      }
                      triggerLabel={`编辑版本 v${version.version_number}`}
                      version={version}
                    />
                  </Tooltip>
                  <Tooltip content="执行试运行，验证配置是否正确">
                    <Button
                      aria-label={`试运行版本 v${version.version_number}`}
                      disabled={dryRunLoading}
                      onClick={() => handleDryRun(version.id)}
                      variant="secondary"
                    >
                      <PlayCircle aria-hidden="true" className="size-4" />
                      试运行
                    </Button>
                  </Tooltip>
                  <Tooltip content="发布此版本，发布后将锁定不可修改">
                    <Button
                      aria-label={`发布版本 v${version.version_number}`}
                      onClick={() => setPublishVersion(version)}
                      variant="primary"
                    >
                      发布
                    </Button>
                  </Tooltip>
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
      {/* 试运行结果 */}
      <Dialog
        onOpenChange={(open) => {
          if (!open) setDryRunResult(null);
        }}
        open={dryRunResult !== null}
      >
        <DialogContent>
          <DialogTitle>试运行结果</DialogTitle>
          <DialogDescription>
            测试计划版本的执行参数预览和有效性校验。
          </DialogDescription>
          <div className="mt-4 space-y-2 text-sm">
            {dryRunResult?.error ? (
              <p className="text-[var(--danger)]">
                {String(dryRunResult.error)}
              </p>
            ) : (
              <>
                <p>
                  状态：
                  <Badge
                    tone={
                      dryRunResult?.status === "published"
                        ? "success"
                        : "warning"
                    }
                  >
                    {String(dryRunResult?.status ?? "")}
                  </Badge>
                </p>
                {dryRunResult?.preview &&
                typeof dryRunResult.preview === "object" ? (
                  <div className="rounded border p-3 space-y-1">
                    {Object.entries(
                      dryRunResult.preview as Record<string, unknown>,
                    ).map(([k, v]) => (
                      <p key={k}>
                        <span className="text-[var(--text-muted)]">{k}：</span>
                        {v === null ? "无" : String(v)}
                      </p>
                    ))}
                  </div>
                ) : null}
                {dryRunResult?.validation &&
                typeof dryRunResult.validation === "object" ? (
                  <div className="rounded border p-3">
                    <p>
                      校验结果：
                      <Badge
                        tone={
                          (dryRunResult.validation as Record<string, unknown>)
                            .valid
                            ? "success"
                            : "danger"
                        }
                      >
                        {(dryRunResult.validation as Record<string, unknown>)
                          .valid
                          ? "通过"
                          : "未通过"}
                      </Badge>
                    </p>
                    {Array.isArray(
                      (dryRunResult.validation as Record<string, unknown>)
                        .errors,
                    ) &&
                    (
                      (dryRunResult.validation as Record<string, unknown>)
                        .errors as string[]
                    ).length > 0 ? (
                      <ul className="mt-2 list-disc pl-4 text-[var(--danger)]">
                        {(
                          (dryRunResult.validation as Record<string, unknown>)
                            .errors as string[]
                        ).map((e, i) => (
                          <li key={i}>{e}</li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ) : null}
              </>
            )}
          </div>
          <div className="mt-5 flex justify-end">
            <Button onClick={() => setDryRunResult(null)}>关闭</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
