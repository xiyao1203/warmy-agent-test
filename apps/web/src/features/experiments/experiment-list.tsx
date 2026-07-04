"use client";

import {
  ArrowDownRight,
  ArrowUpRight,
  Equal,
  FlaskConical,
  Minus,
  PlayCircle,
  Plus,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ListCard, ListCardMeta } from "@/components/ui/list-card";

import type { ExperimentItem } from "./api";
import type { ExperimentRun } from "./api";
import {
  createExperiment,
  listExperimentRuns,
  listExperiments,
  runExperiment,
} from "./api";

const STATUS_TONES: Record<
  string,
  "success" | "warning" | "danger" | "neutral"
> = {
  completed: "success",
  running: "warning",
  failed: "danger",
  pending: "neutral",
};

export function ExperimentList({ projectId }: { projectId: string }) {
  const [experiments, setExperiments] = useState<ExperimentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setExperiments(await listExperiments(projectId));
    } catch {
      /* empty */
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    let active = true;
    void listExperiments(projectId)
      .then((items) => {
        if (active) setExperiments(items);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  async function handleRun(expId: string) {
    await runExperiment(projectId, expId);
    await reload();
  }

  if (loading) {
    return (
      <div className="grid min-h-[40vh] place-items-center text-sm text-[var(--muted)]">
        正在加载实验…
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">实验对比</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            选择两次已完成运行，比较提升、退化和耗时变化，再用于发布判断。
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建对比
        </Button>
      </header>

      <section className="mt-5 grid gap-3 md:grid-cols-4">
        <FlowCard
          description="先产生可对比的结果"
          href={`/projects/${projectId}/runs`}
          icon={<PlayCircle aria-hidden="true" className="size-4" />}
          label="1. 完成两次运行"
        />
        <FlowCard
          description="选择基线和对比运行"
          icon={<FlaskConical aria-hidden="true" className="size-4" />}
          label="2. 创建对比"
        />
        <FlowCard
          description="重点查看失败和退化"
          href={`/projects/${projectId}/experiments`}
          icon={<ArrowDownRight aria-hidden="true" className="size-4" />}
          label="3. 分析退化项"
        />
        <FlowCard
          description="把显著退化拦在发布前"
          href={`/projects/${projectId}/gates`}
          icon={<ShieldCheck aria-hidden="true" className="size-4" />}
          label="4. 配置发布门禁"
        />
      </section>

      {experiments.length === 0 ? (
        <div className="mt-6 rounded-[var(--radius-lg)] border border-dashed border-[var(--hairline)] p-10 text-center">
          <FlaskConical
            aria-hidden="true"
            className="mx-auto size-8 text-[var(--muted)]"
          />
          <p className="mt-3 text-sm font-medium text-[var(--muted)]">
            暂无实验
          </p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            先在运行中心完成两次同一测试计划版本的运行，再创建对比。
          </p>
          <div className="mt-4 flex justify-center gap-2">
            <Button asChild variant="secondary">
              <Link href={`/projects/${projectId}/runs`}>去运行中心</Link>
            </Button>
            <Button onClick={() => setCreateOpen(true)} variant="primary">
              <Plus aria-hidden="true" className="mr-1.5 size-4" />
              创建对比
            </Button>
          </div>
        </div>
      ) : (
        <ul className="mt-6 space-y-3">
          {experiments.map((exp) => (
            <ExperimentCard
              exp={exp}
              key={exp.id}
              onRun={() => handleRun(exp.id)}
              projectId={projectId}
            />
          ))}
        </ul>
      )}

      <CreateExperimentDialog
        onCreated={reload}
        onOpenChange={setCreateOpen}
        open={createOpen}
        projectId={projectId}
      />
    </div>
  );
}

function ExperimentCard({
  exp,
  onRun,
  projectId,
}: {
  exp: ExperimentItem;
  onRun: () => Promise<void>;
  projectId: string;
}) {
  const [running, setRunning] = useState(false);
  const summary = (exp.result_json as Record<string, unknown>).summary as
    | Record<string, number>
    | undefined;

  return (
    <ListCard
      actions={
        <div className="flex items-center gap-1.5">
          {exp.status === "pending" ? (
            <Button
              disabled={running}
              loading={running}
              onClick={async () => {
                setRunning(true);
                try {
                  await onRun();
                } finally {
                  setRunning(false);
                }
              }}
              variant="primary"
            >
              <PlayCircle aria-hidden="true" className="mr-1.5 size-4" />
              生成对比结果
            </Button>
          ) : null}
          <Button asChild className="px-3" variant="secondary">
            <Link href={`/projects/${projectId}/gates`}>配置门禁</Link>
          </Button>
        </div>
      }
      badge={
        <Badge tone={STATUS_TONES[exp.status] ?? "neutral"}>{exp.status}</Badge>
      }
      description={`A: ${exp.run_a_id.slice(0, 8)} · B: ${exp.run_b_id.slice(0, 8)}`}
      footer={
        <>
          <ListCardMeta items={[exp.description ?? undefined]} />
          {summary ? (
            <div className="mt-4 flex flex-wrap gap-4 text-xs">
              <SummaryChip
                icon={<ArrowUpRight className="size-3.5" />}
                label="提升"
                tone="success"
                value={String(summary.improved ?? 0)}
              />
              <SummaryChip
                icon={<ArrowDownRight className="size-3.5" />}
                label="退化"
                tone="danger"
                value={String(summary.degraded ?? 0)}
              />
              <SummaryChip
                icon={<Equal className="size-3.5" />}
                label="无变化"
                tone="neutral"
                value={String(summary.unchanged ?? 0)}
              />
              <SummaryChip
                icon={<Minus className="size-3.5" />}
                label="平均耗时差"
                tone="neutral"
                value={`${summary.avg_duration_delta_ms ?? 0}ms`}
              />
              <SummaryChip
                icon={<Minus className="size-3.5" />}
                label="P50耗时差"
                tone="neutral"
                value={`${summary.p50_duration_delta_ms ?? 0}ms`}
              />
              <SummaryChip
                icon={<Minus className="size-3.5" />}
                label="P95耗时差"
                tone="neutral"
                value={`${summary.p95_duration_delta_ms ?? 0}ms`}
              />
            </div>
          ) : null}
          {(exp.result_json as Record<string, unknown>).case_diffs ? (
            <details className="mt-4">
              <summary className="cursor-pointer text-xs font-medium text-[var(--muted)]">
                查看逐用例提升和退化
              </summary>
              <div className="mt-2 overflow-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[var(--hairline)] text-left text-[var(--muted)]">
                      <th className="pb-1.5 pr-3">用例</th>
                      <th className="pb-1.5 pr-3">状态 A</th>
                      <th className="pb-1.5 pr-3">状态 B</th>
                      <th className="pb-1.5 pr-3">耗时差</th>
                      <th className="pb-1.5">分类</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(
                      (exp.result_json as Record<string, unknown>)
                        .case_diffs as Record<string, unknown>[]
                    ).map((d, i) => (
                      <tr
                        className="border-b border-[var(--hairline)] last:border-0"
                        key={i}
                      >
                        <td className="py-1.5 pr-3 font-mono">
                          {String(d.test_case_id).slice(0, 8)}
                        </td>
                        <td className="py-1.5 pr-3">
                          {String(d.status_a ?? "-")}
                        </td>
                        <td className="py-1.5 pr-3">
                          {String(d.status_b ?? "-")}
                        </td>
                        <td className="py-1.5 pr-3">
                          {String(d.duration_delta_ms)}ms
                        </td>
                        <td className="py-1.5">
                          <Badge
                            tone={
                              d.category === "degraded"
                                ? "danger"
                                : d.category === "improved"
                                  ? "success"
                                  : "neutral"
                            }
                          >
                            {d.category === "degraded"
                              ? "退化"
                              : d.category === "improved"
                                ? "提升"
                                : "无变化"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          ) : null}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link
              className="font-medium text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/runs`}
            >
              查看两次运行结果
            </Link>
            <Link
              className="font-medium text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/test-plans`}
            >
              调整测试计划
            </Link>
          </div>
        </>
      }
      title={exp.name}
    />
  );
}

function SummaryChip({
  icon,
  label,
  tone,
  value,
}: {
  icon: ReactNode;
  label: string;
  tone: "success" | "danger" | "neutral";
  value: string;
}) {
  const color =
    tone === "success"
      ? "text-[var(--success)]"
      : tone === "danger"
        ? "text-[var(--danger)]"
        : "text-[var(--muted)]";
  return (
    <span className={`flex items-center gap-1 ${color}`}>
      {icon}
      <span className="text-[var(--muted)]">{label}:</span>
      <span className="font-semibold">{value}</span>
    </span>
  );
}

function FlowCard({
  description,
  href,
  icon,
  label,
}: {
  description: string;
  href?: string;
  icon: ReactNode;
  label: string;
}) {
  const content = (
    <>
      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)]">
        {icon}
      </span>
      <span className="min-w-0">
        <span className="block font-medium">{label}</span>
        <span className="block truncate text-xs text-[var(--muted)]">
          {description}
        </span>
      </span>
    </>
  );

  if (href) {
    return (
      <Link
        className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm transition-colors hover:border-[var(--primary)]"
        href={href}
      >
        {content}
      </Link>
    );
  }

  return (
    <div className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm">
      {content}
    </div>
  );
}

function CreateExperimentDialog({
  onCreated,
  onOpenChange,
  open,
  projectId,
}: {
  onCreated: () => Promise<unknown>;
  onOpenChange: (open: boolean) => void;
  open: boolean;
  projectId: string;
}) {
  const [name, setName] = useState("");
  const [runAId, setRunAId] = useState("");
  const [runBId, setRunBId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [runs, setRuns] = useState<ExperimentRun[]>([]);

  useEffect(() => {
    if (open)
      void listExperimentRuns(projectId)
        .then(setRuns)
        .catch(() => setRuns([]));
  }, [open, projectId]);

  async function handleCreate() {
    if (!name.trim() || !runAId.trim() || !runBId.trim()) {
      setError("所有字段必填");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await createExperiment(projectId, {
        name: name.trim(),
        run_a_id: runAId.trim(),
        run_b_id: runBId.trim(),
      });
      onOpenChange(false);
      await onCreated();
    } catch {
      setError("创建失败，请检查运行 ID。");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      onOpenChange={(o) => {
        onOpenChange(o);
        if (!o) setError("");
      }}
      open={open}
    >
      <DialogContent>
        <DialogTitle>创建对比</DialogTitle>
        <DialogDescription>
          选择同一测试计划版本下的两次已完成运行，生成提升和退化分析。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            对比名称
            <Input
              className="mt-1.5"
              onChange={(e) => setName(e.target.value)}
              value={name}
            />
          </label>
          <label className="block text-sm font-medium">
            基线运行 A
            <RunSelect onChange={setRunAId} runs={runs} value={runAId} />
          </label>
          <label className="block text-sm font-medium">
            对比运行 B
            <RunSelect onChange={setRunBId} runs={runs} value={runBId} />
          </label>
        </div>
        {error ? (
          <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>
        ) : null}
        <div className="mt-5 flex justify-end gap-2">
          <Button onClick={() => onOpenChange(false)}>取消</Button>
          <Button
            disabled={saving}
            loading={saving}
            onClick={handleCreate}
            variant="primary"
          >
            创建对比
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function RunSelect({
  onChange,
  runs,
  value,
}: {
  onChange: (value: string) => void;
  runs: ExperimentRun[];
  value: string;
}) {
  return (
    <select
      className="mt-1.5 h-9 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] px-3 text-sm"
      onChange={(event) => onChange(event.target.value)}
      value={value}
    >
      <option value="">选择执行记录</option>
      {runs.map((run) => (
        <option key={run.id} value={run.id}>
          {run.status} · {new Date(run.created_at).toLocaleString("zh-CN")}
        </option>
      ))}
    </select>
  );
}
