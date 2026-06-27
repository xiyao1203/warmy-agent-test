"use client";

import type {
  CreateEnvironmentTemplateRequest,
  EnvironmentTemplateResponse,
} from "@warmy/generated-api-client";
import { Cog, Plus, Shield } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
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

type EnvironmentListProps = {
  environments?: EnvironmentTemplateResponse[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateEnvironmentTemplateRequest) => Promise<unknown>;
  onDelete?: (templateId: string) => Promise<unknown>;
  projectId: string;
};

const typeLabels: Record<string, string> = {
  blank: "空环境",
  preset: "预设",
};

export function EnvironmentList({
  environments = [],
  error,
  loading = false,
  onCreate,
  onDelete,
  projectId,
}: EnvironmentListProps) {
  if (loading) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        <p className="text-[var(--text-muted)]">正在加载环境模板…</p>
      </div>
    );
  }
  if (error === "not-found") {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        <p className="text-[var(--text-muted)]">项目不存在或无权访问</p>
      </div>
    );
  }
  if (error === "service") {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        <p className="text-[var(--text-muted)]">环境模板列表暂时不可用</p>
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">环境与凭证</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            管理测试环境模板、测试凭证、Mock 服务和沙箱配置。
          </p>
        </div>
        {onCreate && <CreateTemplateDialog onCreate={onCreate} />}
      </header>

      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {!environments.length ? (
          <EmptyState
            description="创建环境模板后，可在测试计划中引用并自动配置执行环境。"
            title="暂无环境模板"
          />
        ) : (
          <Table className="w-auto min-w-[680px] table-fixed">
            <TableHeader className="bg-[var(--surface-subtle)]">
              <TableRow>
                <TableHead className="w-[420px]">模板信息</TableHead>
                <TableHead className="w-32 text-center">类型</TableHead>
                <TableHead className="w-32 text-center">更新时间</TableHead>
                <TableHead className="w-24 text-center">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {environments.map((template) => (
                <TableRow
                  className="transition-colors hover:bg-[var(--surface-subtle)]"
                  key={template.id}
                >
                  <TableCell>
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-sm)] bg-[var(--surface-subtle)]">
                        <Cog aria-hidden="true" className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-medium">{template.name}</p>
                        <p className="mt-0.5 truncate text-xs text-[var(--text-muted)]">
                          {template.description || "暂无描述"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge
                      tone={
                        template.template_type === "preset"
                          ? "accent"
                          : "neutral"
                      }
                    >
                      {typeLabels[template.template_type] ??
                        template.template_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-center text-sm text-[var(--text-muted)]">
                    {new Date(template.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className="text-center">
                    {onDelete && (
                      <button
                        aria-label={`删除${template.name}`}
                        className="text-sm text-[var(--danger)] hover:underline"
                        onClick={() => onDelete(template.id)}
                      >
                        删除
                      </button>
                    )}
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

function CreateTemplateDialog({
  onCreate,
}: {
  onCreate: (payload: CreateEnvironmentTemplateRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!name.trim()) {
      setError("请输入模板名称");
      return;
    }
    setSubmitting(true);
    try {
      await onCreate({
        description: description.trim() || null,
        name: name.trim(),
        template_type: "blank",
      });
      setOpen(false);
      setName("");
      setDescription("");
      setError("");
    } catch {
      setError("创建失败，请检查输入后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建环境模板
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建环境模板</DialogTitle>
        <DialogDescription>
          环境模板用于定义测试执行时的初始配置，可在测试计划中引用。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            模板名称
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
            <Button
              disabled={submitting}
              onClick={() => setOpen(false)}
              type="button"
            >
              取消
            </Button>
            <Button
              disabled={submitting}
              loading={submitting}
              onClick={submit}
              type="button"
              variant="primary"
            >
              创建模板
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
