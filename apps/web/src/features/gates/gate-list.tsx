"use client";

import {
  CheckCircle2,
  ClipboardCheck,
  PlayCircle,
  Plus,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import { ListCard, ListCardMeta } from "@/components/ui/list-card";
import { ResourceReferenceLink } from "@/components/ui/resource-reference-link";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ResourcePagination } from "@/components/ui/resource-pagination";
import { Skeleton, Tooltip } from "@/components/uiverse";
import { normalizeResourcePage } from "@/lib/pagination";
import { usePaginationState } from "@/lib/use-pagination-state";

import type { GateItem, GateResult, GateRun } from "./api";
import {
  createGate,
  deleteGate,
  evaluateGate,
  listGateRuns,
  listGatePage,
} from "./api";

export function GateList({ projectId }: { projectId: string }) {
  const pagination = usePaginationState();
  const [gates, setGates] = useState<GateItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [runs, setRuns] = useState<GateRun[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<GateItem | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  const [createOpen, setCreateOpen] = useState(false);
  const [evalResult, setEvalResult] = useState<{
    gateId: string;
    result: GateResult;
  } | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listGatePage(
        projectId,
        undefined,
        pagination.page,
        pagination.pageSize,
      );
      const page = normalizeResourcePage(
        response,
        pagination.page,
        pagination.pageSize,
      );
      setGates(page.items);
      setTotal(page.total);
      setTotalPages(page.total_pages);
    } catch {
      /* empty */
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.pageSize, projectId]);

  useEffect(() => {
    let active = true;
    void listGatePage(
      projectId,
      undefined,
      pagination.page,
      pagination.pageSize,
    )
      .then((response) => {
        if (!active) return;
        const page = normalizeResourcePage(
          response,
          pagination.page,
          pagination.pageSize,
        );
        setGates(page.items);
        setTotal(page.total);
        setTotalPages(page.total_pages);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [pagination.page, pagination.pageSize, projectId]);

  useEffect(() => {
    void listGateRuns(projectId)
      .then(setRuns)
      .catch(() => setRuns([]));
  }, [projectId]);

  async function handleDelete(gateId: string) {
    setDeleteBusy(true);
    try {
      await deleteGate(projectId, gateId);
      setDeleteTarget(null);
      await reload();
    } finally {
      setDeleteBusy(false);
    }
  }

  async function handleEvaluate(gate: GateItem, runId: string) {
    try {
      const res = await evaluateGate(projectId, gate.id, {
        run_id: runId,
      });
      setEvalResult({ gateId: gate.id, result: res.result });
    } catch {
      setEvalResult({
        gateId: gate.id,
        result: { passed: false, failures: ["评估失败"] },
      });
    }
  }

  if (loading) {
    return (
      <div className="workspace-page">
        <header className="border-b border-[var(--hairline)] pb-5">
          <Skeleton className="h-7 w-40" />
          <Skeleton className="mt-2 h-4 w-80" />
        </header>
        <div className="mt-5 space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton className="h-20 w-full" key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="workspace-page">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-page-title flex items-center gap-2">
            <ShieldCheck className="size-6" />
            发布门禁
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            用真实运行结果做发布判断，自动检查通过率、关键用例、成本、安全评分和待人工审核。
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} variant="primary">
          <Plus className="mr-1.5 size-4" />
          创建门禁
        </Button>
      </header>

      <section className="mt-5 grid gap-3 md:grid-cols-4">
        <FlowCard
          description="计划版本选择门禁"
          href={`/projects/${projectId}/test-plans`}
          icon={<ClipboardCheck aria-hidden="true" className="size-4" />}
          label="1. 配置测试计划"
        />
        <FlowCard
          description="选择一次真实运行"
          href={`/projects/${projectId}/runs`}
          icon={<PlayCircle aria-hidden="true" className="size-4" />}
          label="2. 查看运行结果"
        />
        <FlowCard
          description="处理安全和人工风险"
          href={`/projects/${projectId}/security`}
          icon={<ShieldAlert aria-hidden="true" className="size-4" />}
          label="3. 补齐风险证据"
        />
        <FlowCard
          description="通过后生成放行结论"
          icon={<ShieldCheck aria-hidden="true" className="size-4" />}
          label="4. 评估发布门禁"
        />
      </section>

      {gates.length === 0 ? (
        <div className="mt-8 rounded-[var(--radius-lg)] border border-dashed border-[var(--hairline)] p-10 text-center">
          <ShieldCheck className="mx-auto size-8 text-[var(--muted)]" />
          <p className="mt-3 text-sm font-medium text-[var(--muted)]">
            暂无门禁
          </p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            先创建门禁，再在测试计划版本里选择它；运行完成后可用真实结果评估是否放行。
          </p>
          <div className="mt-4 flex justify-center gap-3 text-sm">
            <Link
              className="font-medium text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/test-plans`}
            >
              去配置测试计划
            </Link>
            <Link
              className="font-medium text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/runs`}
            >
              去运行中心
            </Link>
          </div>
        </div>
      ) : (
        <ul className="mt-5 space-y-3">
          {gates.map((gate) => (
            <GateCard
              gate={gate}
              key={gate.id}
              onDelete={() => setDeleteTarget(gate)}
              onEvaluate={(runId) => handleEvaluate(gate, runId)}
              projectId={projectId}
              runs={runs}
              result={
                evalResult?.gateId === gate.id ? evalResult.result : undefined
              }
            />
          ))}
        </ul>
      )}

      <div className="mt-4 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        <ResourcePagination
          onPageChange={pagination.setPage}
          onPageSizeChange={pagination.setPageSize}
          page={pagination.page}
          pageSize={pagination.pageSize}
          total={total}
          totalPages={totalPages}
        />
      </div>

      <CreateGateDialog
        onCreated={reload}
        onOpenChange={setCreateOpen}
        open={createOpen}
        projectId={projectId}
      />

      <Dialog
        onOpenChange={() => setDeleteTarget(null)}
        open={deleteTarget !== null}
      >
        <DialogContent>
          <DialogTitle>确认删除</DialogTitle>
          <DialogDescription>
            确定要删除门禁「{deleteTarget?.name}」吗？此操作不可撤销。
          </DialogDescription>
          <div className="mt-5 flex justify-end gap-3">
            <Button onClick={() => setDeleteTarget(null)} variant="secondary">
              取消
            </Button>
            <Button
              loading={deleteBusy}
              onClick={() => {
                if (deleteTarget) void handleDelete(deleteTarget.id);
              }}
              variant="danger"
            >
              确认删除
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function GateCard({
  gate,
  onDelete,
  onEvaluate,
  projectId,
  runs,
  result,
}: {
  gate: GateItem;
  onDelete: () => void;
  onEvaluate: (runId: string) => Promise<void>;
  projectId: string;
  runs: GateRun[];
  result?: GateResult;
}) {
  const [runId, setRunId] = useState("");
  return (
    <ListCard
      actions={
        <>
          <DropdownSelect
            aria-label="选择执行记录"
            className="h-9 min-w-56 rounded border border-[var(--hairline)] bg-[var(--surface)] px-2 text-sm"
            onChange={(event) => setRunId(event.target.value)}
            value={runId}
          >
            <option value="">选择一次真实运行</option>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>
                {run.status} ·{" "}
                {new Date(run.created_at).toLocaleString("zh-CN")}
              </option>
            ))}
          </DropdownSelect>
          <Button
            disabled={!runId}
            onClick={() => onEvaluate(runId)}
            variant="ghost"
          >
            评估运行结果
          </Button>
          <Tooltip content="删除" side="top">
            <Button
              aria-label={`删除门禁 ${gate.name}`}
              className="size-8 shrink-0 px-0"
              onClick={onDelete}
              variant="ghost"
            >
              <Trash2
                aria-hidden="true"
                className="size-4 text-[var(--danger)]"
              />
            </Button>
          </Tooltip>
        </>
      }
      badge={
        gate.enabled ? (
          <Badge tone="success">已启用</Badge>
        ) : (
          <Badge tone="warning">已禁用</Badge>
        )
      }
      description={
        gate.rule_summary ||
        `通过率 ≥ ${(gate.success_rate_threshold * 100).toFixed(0)}%`
      }
      footer={
        <>
          <ListCardMeta
            items={[
              `作用域 ${gate.scope || "project"}`,
              `安全评分 ≥ ${gate.security_threshold.toFixed(1)}`,
              gate.cost_limit != null ? `成本 ≤ ${gate.cost_limit}` : undefined,
              gate.critical_cases.length > 0
                ? `关键用例 ${gate.critical_cases.length} 个`
                : undefined,
              "待人工审核必须清零",
              `最近决策 ${gate.last_decision || "暂无数据"}`,
              `阻塞项 ${gate.blocking_count ?? 0}`,
            ]}
          />
          <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-[var(--muted)]">
            <span>
              证据运行：
              <ResourceReferenceLink reference={gate.last_run_ref} />
            </span>
            <span>
              评估时间{" "}
              {gate.evaluated_at
                ? new Date(gate.evaluated_at).toLocaleString("zh-CN")
                : "暂无数据"}
            </span>
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs">
            <Link
              className="font-medium text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/runs`}
            >
              查看运行结果
            </Link>
            <Link
              className="font-medium text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/security`}
            >
              查看安全发现
            </Link>
            <Link
              className="font-medium text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/reviews`}
            >
              处理人工审核
            </Link>
            <Link
              className="font-medium text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/experiments`}
            >
              查看实验对比
            </Link>
          </div>
          {result ? (
            <div
              className={`mt-3 rounded border p-3 text-sm ${
                result.passed
                  ? "border-[var(--success)] bg-[var(--success-subtle)]"
                  : "border-[var(--danger)] bg-[var(--danger-subtle)]"
              }`}
            >
              <div className="flex items-center gap-2 font-medium">
                {result.passed ? (
                  <CheckCircle2 className="size-4 text-[var(--success)]" />
                ) : (
                  <XCircle className="size-4 text-[var(--danger)]" />
                )}
                {result.passed ? "门禁通过" : "门禁未通过"}
              </div>
              {result.failures.length > 0 ? (
                <ul className="mt-2 list-disc pl-5 text-xs text-[var(--danger)]">
                  {result.failures.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </>
      }
      title={gate.name}
    />
  );
}

function CreateGateDialog({
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
  const [passRate, setPassRate] = useState(0.8);
  const [securityThreshold, setSecurityThreshold] = useState(0.8);
  const [costLimit, setCostLimit] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleCreate() {
    if (!name.trim()) {
      setError("名称不能为空");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await createGate(projectId, {
        name: name.trim(),
        success_rate_threshold: passRate,
        security_threshold: securityThreshold,
        cost_limit: costLimit ? Number(costLimit) : null,
      });
      onOpenChange(false);
      await onCreated();
    } catch {
      setError("创建失败，请重试。");
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
        <DialogTitle>创建发布门禁</DialogTitle>
        <DialogDescription>
          设置发布前必须满足的条件，评估时会读取真实运行、安全测试和人工审核结果。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            名称
            <Input
              className="mt-1.5"
              onChange={(e) => setName(e.target.value)}
              value={name}
            />
          </label>
          <div className="grid grid-cols-2 gap-4">
            <label className="block text-sm font-medium">
              通过率阈值
              <Input
                className="mt-1.5"
                max={1}
                min={0}
                onChange={(e) => setPassRate(Number(e.target.value))}
                step={0.01}
                type="number"
                value={passRate}
              />
            </label>
            <label className="block text-sm font-medium">
              安全评分阈值
              <Input
                className="mt-1.5"
                max={1}
                min={0}
                onChange={(e) => setSecurityThreshold(Number(e.target.value))}
                step={0.01}
                type="number"
                value={securityThreshold}
              />
            </label>
          </div>
          <label className="block text-sm font-medium">
            成本上限（可选）
            <Input
              className="mt-1.5"
              min={0}
              onChange={(e) => setCostLimit(e.target.value)}
              placeholder="留空则不限"
              type="number"
              value={costLimit}
            />
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
            创建
          </Button>
        </div>
      </DialogContent>
    </Dialog>
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
