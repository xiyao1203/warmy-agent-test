"use client";

import type {
  CreateTestPlanRequest,
  TestPlanResponse,
} from "@warmy/generated-api-client";
import { ClipboardCheck, Plus } from "lucide-react";
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

export function TestPlanList({
  error,
  loading = false,
  onCreate = async () => undefined,
  onDelete,
  plans = [],
  projectId,
}: {
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateTestPlanRequest) => Promise<unknown>;
  onDelete?: (planId: string) => Promise<unknown>;
  plans?: TestPlanResponse[];
  projectId: string;
}) {
  if (loading) return <StatusPanel title="正在加载测试计划…" />;
  if (error === "not-found") {
    return <StatusPanel title="项目不存在或你无权访问" />;
  }
  if (error === "service") {
    return <StatusPanel title="测试计划列表暂时不可用" />;
  }
  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">测试计划</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            组合已发布 Agent、数据集和环境，并配置执行门禁。
          </p>
        </div>
        <CreatePlanDialog onCreate={onCreate} />
      </header>
      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {!plans.length ? (
          <EmptyState
            description="创建计划后，为它选择测试资产和运行参数。"
            title="暂无测试计划"
          />
        ) : (
          <Table className="w-auto min-w-[680px] table-fixed">
            <TableHeader className="bg-[var(--surface-subtle)]">
              <TableRow>
                <TableHead className="w-[420px] pl-16">计划信息</TableHead>
                <TableHead className="w-32 text-center">更新时间</TableHead>
                <TableHead className={tableActionHeadClass}>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plans.map((plan) => (
                <TableRow
                  className="transition-colors hover:bg-[var(--surface-subtle)]"
                  key={plan.id}
                >
                  <TableCell>
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-sm)] bg-[var(--surface-subtle)]">
                        <ClipboardCheck aria-hidden="true" className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-medium">{plan.name}</p>
                        <p className="mt-0.5 truncate text-xs text-[var(--text-muted)]">
                          {plan.description || "暂无描述"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-center text-sm text-[var(--text-muted)]">
                    {new Date(plan.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className={tableActionCellClass}>
                    <TableActions label={plan.name}>
                      <Button asChild className="shrink-0 px-2.5" variant="ghost">
                        <Link
                          aria-label={`查看${plan.name}`}
                          href={`/projects/${projectId}/test-plans/${plan.id}`}
                        >
                          查看
                        </Link>
                      </Button>
                      {onDelete ? (
                        <ConfirmDeleteButton
                          label={plan.name}
                          onConfirm={() => onDelete(plan.id)}
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

function CreatePlanDialog({
  onCreate,
}: {
  onCreate: (payload: CreateTestPlanRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!name.trim()) {
      setError("请输入计划名称");
      return;
    }
    setSubmitting(true);
    try {
      await onCreate({
        description: description.trim() || null,
        name: name.trim(),
      });
      setOpen(false);
    } catch {
      setError("创建测试计划失败，请检查输入。");
    } finally {
      setSubmitting(false);
    }
  }
  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建测试计划
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建测试计划</DialogTitle>
        <DialogDescription>计划通过版本保存测试资产和执行参数。</DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            计划名称
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
          {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
          <div className="flex justify-end gap-2">
            <Button disabled={submitting} onClick={() => setOpen(false)}>取消</Button>
            <Button
              disabled={submitting}
              loading={submitting}
              onClick={submit}
              variant="primary"
            >
              保存测试计划
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
        <p className="mt-2 max-w-md text-sm leading-6 text-[var(--text-muted)]">
          请稍后刷新重试，或联系超级管理员。
        </p>
      </div>
    </div>
  );
}
