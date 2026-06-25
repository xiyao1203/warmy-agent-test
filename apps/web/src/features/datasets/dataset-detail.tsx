"use client";

import type {
  CreateTestCaseRequest,
  DatasetResponse,
  DatasetVersionResponse,
  ExportTestCasesResponse,
  ImportTestCasesRequest,
  TestCaseResponse,
} from "@warmy/generated-api-client";
import { ArrowLeft, LockKeyhole, Plus } from "lucide-react";
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
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { ExportButton } from "./export-button";
import { ImportDialog } from "./import-dialog";
import { TestCaseEditor } from "./test-case-editor";

export function DatasetDetail({
  cases = [],
  dataset,
  onCreateCase = async () => undefined,
  onCreateVersion = async () => undefined,
  onDeleteCase = async () => undefined,
  onExport = async () => ({ content: "", format: "json" }),
  onImport = async () => undefined,
  onPublish = async () => undefined,
  onSelectVersion = () => undefined,
  onUpdateCase = async () => undefined,
  selectedVersionId,
  versions = [],
}: {
  cases?: TestCaseResponse[];
  dataset: DatasetResponse;
  onCreateCase?: (
    versionId: string,
    payload: CreateTestCaseRequest,
  ) => Promise<unknown>;
  onCreateVersion?: () => Promise<unknown>;
  onDeleteCase?: (versionId: string, caseId: string) => Promise<unknown>;
  onExport?: (
    versionId: string,
    format: "csv" | "json" | "jsonl",
  ) => Promise<ExportTestCasesResponse>;
  onImport?: (
    versionId: string,
    payload: ImportTestCasesRequest,
  ) => Promise<unknown>;
  onPublish?: (versionId: string) => Promise<unknown>;
  onSelectVersion?: (versionId: string) => void;
  onUpdateCase?: (
    versionId: string,
    caseId: string,
    payload: CreateTestCaseRequest,
  ) => Promise<unknown>;
  selectedVersionId?: string;
  versions?: DatasetVersionResponse[];
}) {
  const [publishVersion, setPublishVersion] =
    useState<DatasetVersionResponse>();
  const selected =
    versions.find((version) => version.id === selectedVersionId) ?? versions[0];
  const editable = selected?.status === "draft";

  return (
    <div className="min-w-0 px-6 py-6">
      <Link
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
        href={`/projects/${dataset.project_id}/datasets`}
      >
        <ArrowLeft aria-hidden="true" className="size-4" />
        返回数据集列表
      </Link>
      <header className="mt-4 flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {dataset.name}
          </h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {dataset.description || "暂无描述"}
          </p>
        </div>
        <Button onClick={onCreateVersion} variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建版本
        </Button>
      </header>

      <div
        aria-label="数据集版本"
        className="mt-5 flex flex-wrap items-center gap-2"
        role="tablist"
      >
        {versions.map((version) => (
          <button
            aria-selected={version.id === selected?.id}
            className={`rounded-[var(--radius-sm)] border px-3 py-1.5 text-sm ${
              version.id === selected?.id
                ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent-text)]"
                : "border-[var(--border)] bg-[var(--surface)]"
            }`}
            key={version.id}
            onClick={() => onSelectVersion(version.id)}
            role="tab"
            type="button"
          >
            v{version.version_number}{" "}
            {version.status === "published" ? "已发布" : "草稿"}
          </button>
        ))}
      </div>

      {selected ? (
        <>
          <section className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-4 py-3">
            <div className="flex items-center gap-2">
              <Badge tone={editable ? "warning" : "success"}>
                {editable ? "草稿可编辑" : "只读版本"}
              </Badge>
              {!editable ? (
                <span className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)]">
                  <LockKeyhole aria-hidden="true" className="size-3.5" />
                  发布后已锁定
                </span>
              ) : null}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {editable ? (
                <>
                  <TestCaseEditor
                    onSubmit={(payload) => onCreateCase(selected.id, payload)}
                    triggerLabel="添加用例"
                  />
                  <ImportDialog
                    onImport={(payload) => onImport(selected.id, payload)}
                  />
                  <Button
                    aria-label={`发布 v${selected.version_number}`}
                    onClick={() => setPublishVersion(selected)}
                    variant="primary"
                  >
                    发布
                  </Button>
                </>
              ) : null}
              <ExportButton
                onExport={(format) => onExport(selected.id, format)}
              />
            </div>
          </section>

          <section className="mt-4 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
            {!cases.length ? (
              <EmptyState
                description={
                  editable
                    ? "添加或导入第一条测试用例。"
                    : "此版本没有测试用例。"
                }
                title="暂无测试用例"
              />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>用例</TableHead>
                    <TableHead>模式</TableHead>
                    <TableHead>优先级</TableHead>
                    <TableHead>标签</TableHead>
                    <TableHead className="w-24 text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cases.map((caseItem) => (
                    <TableRow key={caseItem.id}>
                      <TableCell>
                        <p className="font-medium">{caseItem.name}</p>
                        <p className="mt-0.5 max-w-xl truncate font-mono text-xs text-[var(--text-muted)]">
                          {JSON.stringify(caseItem.input)}
                        </p>
                      </TableCell>
                      <TableCell>
                        {caseItem.execution_mode === "api" ? "API" : "浏览器"}
                      </TableCell>
                      <TableCell>{caseItem.priority || "—"}</TableCell>
                      <TableCell>{caseItem.tags.join(", ") || "—"}</TableCell>
                      <TableCell className="text-right">
                        {editable ? (
                          <div className="flex justify-end gap-1">
                            <TestCaseEditor
                              caseItem={caseItem}
                              onSubmit={(payload) =>
                                onUpdateCase(selected.id, caseItem.id, payload)
                              }
                              triggerLabel="编辑"
                            />
                            <Button
                              aria-label={`删除用例 ${caseItem.name}`}
                              onClick={() =>
                                onDeleteCase(selected.id, caseItem.id)
                              }
                              variant="danger"
                            >
                              删除
                            </Button>
                          </div>
                        ) : (
                          <span className="text-xs text-[var(--text-muted)]">
                            只读
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </section>
        </>
      ) : (
        <div className="mt-5 rounded-[var(--radius-md)] border border-[var(--border)] p-8 text-center">
          <p className="text-sm font-medium">暂无版本</p>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            创建版本后即可维护测试用例。
          </p>
        </div>
      )}

      <Dialog
        onOpenChange={(open) => {
          if (!open) setPublishVersion(undefined);
        }}
        open={Boolean(publishVersion)}
      >
        <DialogContent>
          <DialogTitle>发布数据集版本</DialogTitle>
          <DialogDescription>发布后用例将不可编辑。</DialogDescription>
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
