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

type AgentListProps = {
  agents?: AgentResponse[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateAgentRequest) => Promise<unknown>;
  onDelete?: (agentId: string) => void;
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
  projectId,
}: AgentListProps) {
  if (loading) return <StatusPanel title="正在加载 Agent…" />;
  if (error === "not-found") {
    return <StatusPanel title="项目不存在或你无权访问" />;
  }
  if (error === "service") {
    return <StatusPanel title="Agent 列表暂时不可用" />;
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
        <CreateAgentDialog onCreate={onCreate} />
      </header>
      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {!agents.length ? (
          <EmptyState
            description="创建 Agent 后，再为它配置并发布可复现版本。"
            title="暂无 Agent"
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agent</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>最近更新</TableHead>
                <TableHead className="w-24 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {agents.map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <span className="grid size-8 place-items-center rounded-[var(--radius-sm)] bg-[var(--surface-subtle)]">
                        <Bot aria-hidden="true" className="size-4" />
                      </span>
                      <div>
                        <p className="font-medium">{agent.name}</p>
                        <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                          {agent.description || "暂无描述"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge tone={agent.agent_type === "canvas" ? "accent" : "neutral"}>
                      {typeLabels[agent.agent_type]}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-[var(--text-muted)]">
                    {new Date(agent.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button asChild variant="ghost">
                        <Link href={`/projects/${projectId}/agents/${agent.id}`}>
                          查看
                        </Link>
                      </Button>
                      {onDelete ? (
                        <Button
                          onClick={() => onDelete(agent.id)}
                          variant="danger"
                        >
                          删除
                        </Button>
                      ) : null}
                    </div>
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

  async function submit() {
    if (!name.trim()) {
      setError("请输入 Agent 名称");
      return;
    }
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
            <Button onClick={() => setOpen(false)} type="button">
              取消
            </Button>
            <Button onClick={submit} type="button" variant="primary">
              保存 Agent
            </Button>
          </div>
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
