"use client";

import type {
  CreateTestPlanRequest,
  TestPlanResponse,
} from "@warmy/generated-api-client";
import {
  ClipboardCheck,
  Database,
  PlayCircle,
  Plus,
  Settings2,
  Trash2,
} from "lucide-react";
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
  TableActionButton,
  tableActionCellClass,
} from "@/components/ui/table-actions";
import { TruncatedText } from "@/components/ui/truncated-text";

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
      <header className="flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">测试计划</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            每个计划都要绑定已发布 Agent、用例集版本、环境、评分器和发布门禁。
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button asChild variant="secondary">
            <Link href={`/projects/${projectId}/datasets`}>
              <Database aria-hidden="true" className="mr-1.5 size-4" />
              管理用例集
            </Link>
          </Button>
          <CreatePlanDialog onCreate={onCreate} />
        </div>
      </header>
      <section className="mt-5 grid gap-3 md:grid-cols-3">
        <Link
          className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm transition-colors hover:border-[var(--primary)]"
          href={`/projects/${projectId}/agents`}
        >
          <Settings2
            aria-hidden="true"
            className="size-4 shrink-0 text-[var(--primary)]"
          />
          <span className="min-w-0">
            <span className="block font-medium">选择待测 Agent</span>
            <span className="block truncate text-xs text-[var(--muted)]">
              使用已发布版本
            </span>
          </span>
        </Link>
        <Link
          className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm transition-colors hover:border-[var(--primary)]"
          href={`/projects/${projectId}/datasets`}
        >
          <Database
            aria-hidden="true"
            className="size-4 shrink-0 text-[var(--primary)]"
          />
          <span className="min-w-0">
            <span className="block font-medium">准备用例集</span>
            <span className="block truncate text-xs text-[var(--muted)]">
              发布后供计划选择
            </span>
          </span>
        </Link>
        <Link
          className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm transition-colors hover:border-[var(--primary)]"
          href={`/projects/${projectId}/runs`}
        >
          <PlayCircle
            aria-hidden="true"
            className="size-4 shrink-0 text-[var(--primary)]"
          />
          <span className="min-w-0">
            <span className="block font-medium">查看测试执行</span>
            <span className="block truncate text-xs text-[var(--muted)]">
              发布版本后运行
            </span>
          </span>
        </Link>
      </section>
      <section className="mt-5 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        {!plans.length ? (
          <EmptyState
            action={
              <div className="flex flex-wrap justify-center gap-2">
                <Button asChild variant="secondary">
                  <Link href={`/projects/${projectId}/datasets`}>
                    去准备用例集
                  </Link>
                </Button>
              </div>
            }
            description="先创建计划，再进入计划详情选择 Agent、用例集版本、环境、评分器和门禁。"
            title="暂无测试计划"
          />
        ) : (
          <Table className="w-full table-fixed">
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead className="w-[54%]">计划信息</TableHead>
                <TableHead className="w-[20%]">更新时间</TableHead>
                <TableHead className="w-[26%] whitespace-nowrap">
                  下一步
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plans.map((plan) => (
                <TableRow
                  className="transition-colors hover:bg-[var(--canvas-soft)]"
                  key={plan.id}
                >
                  <TableCell>
                    <div className="mx-auto flex w-fit max-w-full min-w-0 items-center gap-3 text-left">
                      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--canvas-soft)]">
                        <ClipboardCheck aria-hidden="true" className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <TruncatedText className="font-medium">
                          {plan.name}
                        </TruncatedText>
                        <TruncatedText className="mt-0.5 text-xs text-[var(--muted)]">
                          {plan.description || "暂无描述"}
                        </TruncatedText>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-center text-sm text-[var(--muted)]">
                    {new Date(plan.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className={tableActionCellClass}>
                    <TableActions label={plan.name}>
                      <TableActionButton asChild label={`配置${plan.name}`}>
                        <Link
                          href={`/projects/${projectId}/test-plans/${plan.id}`}
                        >
                          <Settings2 aria-hidden="true" />
                        </Link>
                      </TableActionButton>
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
        <DialogDescription>
          计划通过版本保存测试资产和执行参数。
        </DialogDescription>
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
          className="size-8 shrink-0 border-transparent bg-transparent p-0 hover:bg-[var(--danger-subtle)]"
          variant="danger"
        >
          <Trash2 aria-hidden="true" className="size-4" />
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
