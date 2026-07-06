"use client";

import type {
  CreateDatasetRequest,
  DatasetResponse,
} from "@warmy/generated-api-client";
import { Database, Plus } from "lucide-react";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  TableActions,
  tableActionCellClass,
  tableActionHeadClass,
} from "@/components/ui/table-actions";
import { Skeleton, Tooltip } from "@/components/uiverse";

export function DatasetList({
  datasets = [],
  error,
  loading = false,
  onCreate = async () => undefined,
  onDelete,
  projectId,
}: {
  datasets?: DatasetResponse[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateDatasetRequest) => Promise<unknown>;
  onDelete?: (datasetId: string) => Promise<unknown>;
  projectId: string;
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
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">测试用例</h1>
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
          <Table className="w-full table-fixed">
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead className="w-[54%]">用例集信息</TableHead>
                <TableHead className="w-[20%]">更新时间</TableHead>
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
                        <p className="truncate font-medium">{dataset.name}</p>
                        <p className="mt-0.5 truncate text-xs text-[var(--muted)]">
                          {dataset.description || "暂无描述"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-center text-sm text-[var(--muted)]">
                    {new Date(dataset.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className={tableActionCellClass}>
                    <TableActions label={dataset.name}>
                      <Button
                        asChild
                        className="shrink-0 px-2.5"
                        variant="ghost"
                      >
                        <Link
                          aria-label={`管理${dataset.name}用例`}
                          href={`/projects/${projectId}/datasets/${dataset.id}`}
                        >
                          管理用例
                        </Link>
                      </Button>
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
      </section>
    </div>
  );
}

function CreateDatasetDialog({
  onCreate,
}: {
  onCreate: (payload: CreateDatasetRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
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
      <DialogTrigger asChild>
        <Button
          aria-label={`删除${label}`}
          className="shrink-0 border-transparent bg-transparent px-2.5 hover:bg-[var(--danger-subtle)]"
          variant="danger"
        >
          删除
        </Button>
      </DialogTrigger>
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
    <div className="min-w-0 px-6 py-6">
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
