"use client";

import type { RunResponse } from "@warmy/generated-api-client";
import { Activity, Play, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type PlanVersionOption = { id: string; label: string };

export function RunCenter({
  error,
  loading = false,
  onCreate = async () => undefined,
  planVersions = [],
  projectId,
  runs = [],
}: {
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (testPlanVersionId: string) => Promise<unknown>;
  planVersions?: PlanVersionOption[];
  projectId: string;
  runs?: RunResponse[];
}) {
  const [versionId, setVersionId] = useState(planVersions[0]?.id ?? "");
  const [busy, setBusy] = useState(false);
  if (loading) return <StatusPanel title="正在加载运行中心…" />;
  if (error === "not-found") return <StatusPanel title="项目不存在或你无权访问" />;
  if (error === "service") return <StatusPanel title="运行中心暂时不可用" />;
  async function submit() {
    if (!versionId) return;
    setBusy(true);
    try {
      await onCreate(versionId);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">运行中心</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            基于已发布测试计划启动 API Agent 执行，并查看进度、结果与 Trace。
          </p>
        </div>
        <div className="flex items-end gap-2">
          <label className="text-sm font-medium">
            测试计划版本
            <select
              className="mt-1.5 h-9 min-w-56 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-2 text-sm"
              onChange={(event) => setVersionId(event.target.value)}
              value={versionId}
            >
              <option value="">请选择已发布版本</option>
              {planVersions.map((version) => (
                <option key={version.id} value={version.id}>
                  {version.label}
                </option>
              ))}
            </select>
          </label>
          <Button disabled={!versionId || busy} onClick={submit} variant="primary">
            <Play aria-hidden="true" className="mr-1.5 size-4" />
            开始运行
          </Button>
        </div>
      </header>
      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {!runs.length ? (
          <EmptyState
            description="选择一个已发布测试计划版本后启动首个运行。"
            title="暂无运行记录"
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>运行</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>进度</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="w-24 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <span className="grid size-8 place-items-center rounded-[var(--radius-sm)] bg-[var(--surface-subtle)]">
                        <Activity aria-hidden="true" className="size-4" />
                      </span>
                      <div>
                        <p className="font-medium">Run {run.id.slice(0, 8)}</p>
                        <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                          Workflow {run.workflow_id ?? "待启动"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={run.status} />
                  </TableCell>
                  <TableCell className="text-sm">
                    {run.passed_cases + run.failed_cases + run.error_cases + run.cancelled_cases} /{" "}
                    {run.total_cases}
                  </TableCell>
                  <TableCell className="text-sm text-[var(--text-muted)]">
                    {new Date(run.created_at).toLocaleString("zh-CN")}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button asChild variant="ghost">
                      <Link href={`/projects/${projectId}/runs/${run.id}`}>查看</Link>
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

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "passed"
      ? "success"
      : status === "failed" || status === "error"
        ? "danger"
        : status === "cancelled"
          ? "warning"
          : "accent";
  return (
    <Badge tone={tone}>
      <RotateCcw aria-hidden="true" className="mr-1 size-3" />
      {status}
    </Badge>
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

