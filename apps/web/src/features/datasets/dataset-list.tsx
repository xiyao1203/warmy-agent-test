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

export function DatasetList({
  datasets = [],
  error,
  loading = false,
  onCreate = async () => undefined,
  projectId,
}: {
  datasets?: DatasetResponse[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateDatasetRequest) => Promise<unknown>;
  projectId: string;
}) {
  if (loading) return <StatusPanel title="正在加载数据集…" />;
  if (error === "not-found") {
    return <StatusPanel title="项目不存在或你无权访问" />;
  }
  if (error === "service") {
    return <StatusPanel title="数据集列表暂时不可用" />;
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">数据集与用例</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            管理 API 与浏览器测试用例、导入导出和不可变版本。
          </p>
        </div>
        <CreateDatasetDialog onCreate={onCreate} />
      </header>
      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {!datasets.length ? (
          <EmptyState
            description="创建数据集后，可添加或批量导入测试用例。"
            title="暂无数据集"
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>数据集</TableHead>
                <TableHead>最近更新</TableHead>
                <TableHead className="w-24 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datasets.map((dataset) => (
                <TableRow key={dataset.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <span className="grid size-8 place-items-center rounded-[var(--radius-sm)] bg-[var(--surface-subtle)]">
                        <Database aria-hidden="true" className="size-4" />
                      </span>
                      <div>
                        <p className="font-medium">{dataset.name}</p>
                        <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                          {dataset.description || "暂无描述"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-[var(--text-muted)]">
                    {new Date(dataset.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button asChild variant="ghost">
                      <Link
                        href={`/projects/${projectId}/datasets/${dataset.id}`}
                      >
                        查看
                      </Link>
                    </Button>
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

  async function submit() {
    if (!name.trim()) {
      setError("请输入数据集名称");
      return;
    }
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
      setError("创建数据集失败，请检查输入后重试。");
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建数据集
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建数据集</DialogTitle>
        <DialogDescription>
          数据集通过版本管理用例，发布后保持只读。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            数据集名称
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
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button onClick={submit} variant="primary">
              保存数据集
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function StatusPanel({ title }: { title: string }) {
  return (
    <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
      {title}
    </div>
  );
}
