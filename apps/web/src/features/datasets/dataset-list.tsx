"use client";

import type {
  CreateDatasetRequest,
  DatasetResponse,
} from "@warmy/generated-api-client";
import { Database, ListChecks, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { ResourceReferenceLink } from "@/components/ui/resource-reference-link";
import { ResourcePagination } from "@/components/ui/resource-pagination";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableValue,
} from "@/components/ui/table";
import {
  TableActions,
  TableActionButton,
  tableActionCellClass,
  tableActionHeadClass,
} from "@/components/ui/table-actions";
import { TruncatedText } from "@/components/ui/truncated-text";
import { Skeleton, Tooltip } from "@/components/uiverse";
import { useCreateIntent } from "@/lib/use-create-intent";
import type { PageSize } from "@/lib/pagination";

export function DatasetList({
  datasets = [],
  error,
  loading = false,
  onCreate = async () => undefined,
  onDelete,
  onPageChange = () => undefined,
  onPageSizeChange = () => undefined,
  page = 1,
  pageSize = 10,
  projectId,
  total = datasets.length,
  totalPages = datasets.length ? 1 : 0,
}: {
  datasets?: DatasetResponse[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateDatasetRequest) => Promise<unknown>;
  onDelete?: (datasetId: string) => Promise<unknown>;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: PageSize) => void;
  page?: number;
  pageSize?: PageSize;
  projectId: string;
  total?: number;
  totalPages?: number;
}) {
  if (loading)
    return (
      <>
        <span className="sr-only">正在加载用例集…</span>
        <DatasetListSkeleton />
      </>
    );
  if (error === "not-found") {
    return <StatusPanel title="项目不存在或你无权访问" />;
  }
  if (error === "service") {
    return <StatusPanel title="用例集列表暂时不可用" />;
  }

  return (
    <div className="workspace-page">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-page-title">测试用例</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            一个用例集包含多条用例，发布后可直接用于测试计划。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Tooltip content="创建新的用例集">
            <CreateDatasetDialog onCreate={onCreate} />
          </Tooltip>
        </div>
      </header>
      <section className="mt-5 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        {!datasets.length ? (
          <EmptyState
            description="先创建用例集，再新增或批量导入测试用例。"
            title="暂无用例集"
          />
        ) : (
          <Table className="w-full">
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead className="min-w-60">用例集信息</TableHead>
                <TableHead className="min-w-40">最新版本</TableHead>
                <TableHead className="min-w-64">用例覆盖</TableHead>
                <TableHead className="whitespace-nowrap">更新时间</TableHead>
                <TableHead className={tableActionHeadClass}>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datasets.map((dataset) => (
                <TableRow
                  className="transition-colors hover:bg-[var(--canvas-soft)]"
                  key={dataset.id}
                >
                  <TableCell>
                    <div className="mx-auto flex w-fit max-w-full min-w-0 items-center gap-3 text-left">
                      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--canvas-soft)]">
                        <Database aria-hidden="true" className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <TruncatedText className="font-medium">
                          {dataset.name}
                        </TruncatedText>
                        <TruncatedText className="mt-0.5 text-xs text-[var(--muted)]">
                          {dataset.description || "暂无描述"}
                        </TruncatedText>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <TableValue className="text-xs">
                      <ResourceReferenceLink
                        reference={dataset.latest_version}
                      />
                      <p className="mt-1 text-[var(--muted)]">
                        发布于{" "}
                        {dataset.published_at
                          ? new Date(dataset.published_at).toLocaleDateString(
                              "zh-CN",
                            )
                          : "暂无数据"}
                      </p>
                    </TableValue>
                  </TableCell>
                  <TableCell>
                    <TableValue className="text-xs leading-5 text-[var(--muted)]">
                      <p>
                        用例 {dataset.case_count ?? 0} · 就绪{" "}
                        {dataset.ready_count ?? 0} · API{" "}
                        {dataset.api_count ?? 0} · 浏览器{" "}
                        {dataset.browser_count ?? 0} · Codex{" "}
                        {dataset.codex_explore_count ?? 0}
                      </p>
                      <p>
                        优先级：{formatDistribution(dataset.priority_coverage)}
                      </p>
                      <p>
                        来源：{formatDistribution(dataset.source_distribution)}
                      </p>
                    </TableValue>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-center text-sm text-[var(--muted)]">
                    {new Date(dataset.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className={tableActionCellClass}>
                    <TableActions label={dataset.name}>
                      <TableActionButton
                        accessibleLabel={`管理${dataset.name}用例`}
                        asChild
                        label="管理"
                      >
                        <Link
                          href={`/projects/${projectId}/datasets/${dataset.id}`}
                        >
                          <ListChecks aria-hidden="true" />
                        </Link>
                      </TableActionButton>
                      {onDelete ? (
                        <ConfirmDeleteButton
                          label={dataset.name}
                          onConfirm={() => onDelete(dataset.id)}
                        />
                      ) : null}
                    </TableActions>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
        <ResourcePagination
          onPageChange={onPageChange}
          onPageSizeChange={onPageSizeChange}
          page={page}
          pageSize={pageSize}
          total={total}
          totalPages={totalPages}
        />
      </section>
    </div>
  );
}

function formatDistribution(values?: Record<string, number>) {
  const entries = Object.entries(values ?? {});
  return entries.length
    ? entries.map(([key, value]) => `${key} ${value}`).join(" · ")
    : "暂无数据";
}

function CreateDatasetDialog({
  onCreate,
}: {
  onCreate: (payload: CreateDatasetRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useCreateIntent("dataset");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!name.trim()) {
      setError("请输入用例集名称");
      return;
    }
    setSubmitting(true);
    try {
      await onCreate({
        description: description.trim() || null,
        name: name.trim(),
      });
      setOpen(false);
      setName("");
      setDescription("");
      setError("");
    } catch {
      setError("创建用例集失败，请检查输入后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建用例集
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建用例集</DialogTitle>
        <DialogDescription>
          用例集负责收纳测试用例，发布后保持只读并供测试计划引用。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            用例集名称
            <Input
              className="mt-1.5"
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="block text-sm font-medium">
            描述
            <Input
              className="mt-1.5"
              onChange={(event) => setDescription(event.target.value)}
              value={description}
            />
          </label>
          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button disabled={submitting} onClick={() => setOpen(false)}>
              取消
            </Button>
            <Button
              disabled={submitting}
              loading={submitting}
              onClick={submit}
              variant="primary"
            >
              保存用例集
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ConfirmDeleteButton({
  label,
  onConfirm,
}: {
  label: string;
  onConfirm: () => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <Tooltip content="删除" side="top">
        <DialogTrigger asChild>
          <Button
            aria-label={`删除${label}`}
            className="size-8 shrink-0 border-transparent bg-transparent p-0 hover:bg-[var(--danger-subtle)]"
            variant="danger"
          >
            <Trash2 aria-hidden="true" className="size-4" />
          </Button>
        </DialogTrigger>
      </Tooltip>
      <DialogContent>
        <DialogTitle>确认删除</DialogTitle>
        <DialogDescription>
          确定要删除「{label}」吗？此操作不可恢复。
        </DialogDescription>
        <div className="mt-5 flex justify-end gap-2">
          <Button disabled={deleting} onClick={() => setOpen(false)}>
            取消
          </Button>
          <Button
            disabled={deleting}
            loading={deleting}
            onClick={async () => {
              setDeleting(true);
              try {
                await onConfirm();
                setOpen(false);
              } finally {
                setDeleting(false);
              }
            }}
            variant="danger"
          >
            确认删除
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function StatusPanel({ title }: { title: string }) {
  return (
    <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
      <div>
        <h1 className="text-base font-semibold">{title}</h1>
        <p className="mt-2 max-w-md text-sm leading-6 text-[var(--muted)]">
          请稍后刷新重试，或联系超级管理员。
        </p>
      </div>
    </div>
  );
}

function DatasetListSkeleton() {
  return (
    <div className="workspace-page">
      {/* Header skeleton */}
      <header className="flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <Skeleton className="h-8 w-40" />
          <Skeleton className="mt-2 h-4 w-56" />
        </div>
        <Skeleton className="h-9 w-24" />
      </header>

      {/* Table skeleton */}
      <section className="mt-5 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        <div className="p-4">
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-20" />
                <Skeleton className="ml-auto h-4 w-16" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
