"use client";

import type {
  AgentResponse,
  AgentType,
  CreateAgentRequest,
} from "@warmy/generated-api-client";
import { Bot, Plus } from "lucide-react";
import Link from "next/link";
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
import {
  TableActions,
  tableActionCellClass,
  tableActionHeadClass,
} from "@/components/ui/table-actions";
import { Skeleton, SkeletonText, Tooltip } from "@/components/uiverse";

type AgentListProps = {
  agents?: AgentResponse[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateAgentRequest) => Promise<unknown>;
  onDelete?: (agentId: string) => Promise<unknown>;
  onRetry?: () => void;
  projectId: string;
};

const typeLabels: Record<AgentType, string> = {
  canvas: "画布 Agent",
  generic_http: "通用 HTTP",
};

export function AgentList({
  agents = [],
  error,
  loading = false,
  onCreate = async () => undefined,
  onDelete,
  onRetry,
  projectId,
}: AgentListProps) {
  if (loading) return <AgentListSkeleton />;
  if (error === "not-found") {
    return <StatusPanel title="项目不存在或你无权访问" />;
  }
  if (error === "service") {
    return <StatusPanel onRetry={onRetry} title="Agent 列表暂时不可用" />;
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Agent 与版本</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            管理待测 Agent、连接配置和不可变发布版本。
          </p>
        </div>
        <Tooltip content="创建新的 Agent 配置">
          <CreateAgentDialog onCreate={onCreate} />
        </Tooltip>
      </header>
      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {!agents.length ? (
          <EmptyState
            description="创建 Agent 后，再为它配置并发布可复现版本。"
            title="暂无 Agent"
          />
        ) : (
          <Table className="w-auto min-w-[760px] table-fixed">
            <TableHeader className="bg-[var(--surface-subtle)]">
              <TableRow>
                <TableHead className="w-[360px] pl-16">智能体信息</TableHead>
                <TableHead className="w-36 text-center">接入类型</TableHead>
                <TableHead className="w-32 text-center">更新时间</TableHead>
                <TableHead className={tableActionHeadClass}>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {agents.map((agent) => (
                <TableRow
                  className="transition-colors hover:bg-[var(--surface-subtle)]"
                  key={agent.id}
                >
                  <TableCell>
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-sm)] bg-[var(--surface-subtle)]">
                        <Bot aria-hidden="true" className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-medium">{agent.name}</p>
                        <p className="mt-0.5 truncate text-xs text-[var(--text-muted)]">
                          {agent.description || "暂无描述"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge tone={agent.agent_type === "canvas" ? "accent" : "neutral"}>
                      {typeLabels[agent.agent_type]}
                    </Badge>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-center text-sm text-[var(--text-muted)]">
                    {new Date(agent.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className={tableActionCellClass}>
                    <TableActions label={agent.name}>
                      <Button asChild className="shrink-0 px-2.5" variant="ghost">
                        <Link
                          aria-label={`查看${agent.name}`}
                          href={`/projects/${projectId}/agents/${agent.id}`}
                        >
                          查看
                        </Link>
                      </Button>
                      {onDelete ? (
                        <ConfirmDeleteButton
                          label={agent.name}
                          onConfirm={() => onDelete(agent.id)}
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

function CreateAgentDialog({
  onCreate,
}: {
  onCreate: (payload: CreateAgentRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [agentType, setAgentType] = useState<AgentType>("generic_http");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!name.trim()) {
      setError("请输入 Agent 名称");
      return;
    }
    setSubmitting(true);
    try {
      await onCreate({
        agent_type: agentType,
        description: description.trim() || null,
        name: name.trim(),
      });
      setOpen(false);
      setName("");
      setDescription("");
      setError("");
    } catch {
      setError("创建 Agent 失败，请检查输入后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建 Agent
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建 Agent</DialogTitle>
        <DialogDescription>先登记 Agent，再创建具体连接版本。</DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            Agent 名称
            <Input
              className="mt-1.5"
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="block text-sm font-medium">
            Agent 类型
            <select
              className="mt-1.5 h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] hover:border-[var(--border-strong)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
              onChange={(event) => setAgentType(event.target.value as AgentType)}
              value={agentType}
            >
              <option value="generic_http">通用 HTTP</option>
              <option value="canvas">画布 Agent</option>
            </select>
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
            <Button disabled={submitting} onClick={() => setOpen(false)} type="button">
              取消
            </Button>
            <Button
              disabled={submitting}
              loading={submitting}
              onClick={submit}
              type="button"
              variant="primary"
            >
              保存 Agent
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

function StatusPanel({ onRetry, title }: { onRetry?: () => void; title: string }) {
  return (
    <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
      <div>
        <h1 className="text-base font-semibold">{title}</h1>
        <p className="mt-2 max-w-md text-sm leading-6 text-[var(--text-muted)]">
          请稍后刷新重试，或联系超级管理员。
        </p>
        {onRetry ? (
          <Button className="mt-4" onClick={onRetry} variant="secondary">
            重试
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function AgentListSkeleton() {
  return (
    <div className="min-w-0 px-6 py-6">
      {/* Header skeleton */}
      <header className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="mt-2 h-4 w-64" />
        </div>
        <Skeleton className="h-9 w-24" />
      </header>

      {/* Table skeleton */}
      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="p-4">
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-4 w-32" />
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
