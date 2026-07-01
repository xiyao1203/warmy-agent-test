"use client";

import { CheckCircle2, Plus, ShieldCheck, Trash2, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ListCard, ListCardMeta } from "@/components/ui/list-card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Tooltip } from "@/components/uiverse";

import type { GateItem, GateResult, GateRun } from "./api";
import {
  createGate,
  deleteGate,
  evaluateGate,
  listGateRuns,
  listGates,
} from "./api";

export function GateList({ projectId }: { projectId: string }) {
  const [gates, setGates] = useState<GateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [runs, setRuns] = useState<GateRun[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [evalResult, setEvalResult] = useState<{
    gateId: string;
    result: GateResult;
  } | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setGates(await listGates(projectId));
    } catch {
      /* empty */
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    let active = true;
    void listGates(projectId)
      .then((items) => {
        if (active) setGates(items);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  useEffect(() => {
    void listGateRuns(projectId)
      .then(setRuns)
      .catch(() => setRuns([]));
  }, [projectId]);

  async function handleDelete(gateId: string) {
    if (!confirm("确定删除此门禁？")) return;
    await deleteGate(projectId, gateId);
    await reload();
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
      <div className="grid min-h-[40vh] place-items-center text-sm text-[var(--muted)]">
        正在加载发布门禁…
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <ShieldCheck className="size-6" />
            发布门禁
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            配置发布前必须满足的条件：通过率、关键用例、成本、安全评分。
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} variant="primary">
          <Plus className="mr-1.5 size-4" />
          创建门禁
        </Button>
      </header>

      {gates.length === 0 ? (
        <div className="mt-8 rounded-[var(--radius-lg)] border border-dashed border-[var(--hairline)] p-10 text-center">
          <ShieldCheck className="mx-auto size-8 text-[var(--muted)]" />
          <p className="mt-3 text-sm font-medium text-[var(--muted)]">
            暂无门禁
          </p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            点击「创建门禁」配置发布条件。
          </p>
        </div>
      ) : (
        <ul className="mt-5 space-y-3">
          {gates.map((gate) => (
            <GateCard
              gate={gate}
              key={gate.id}
              onDelete={() => handleDelete(gate.id)}
              onEvaluate={(runId) => handleEvaluate(gate, runId)}
              runs={runs}
              result={
                evalResult?.gateId === gate.id ? evalResult.result : undefined
              }
            />
          ))}
        </ul>
      )}

      <CreateGateDialog
        onCreated={reload}
        onOpenChange={setCreateOpen}
        open={createOpen}
        projectId={projectId}
      />
    </div>
  );
}

function GateCard({
  gate,
  onDelete,
  onEvaluate,
  runs,
  result,
}: {
  gate: GateItem;
  onDelete: () => Promise<void>;
  onEvaluate: (runId: string) => Promise<void>;
  runs: GateRun[];
  result?: GateResult;
}) {
  const [runId, setRunId] = useState("");
  return (
    <ListCard
      actions={
        <>
          <select
            aria-label="选择执行记录"
            className="h-9 max-w-48 rounded border border-[var(--hairline)] bg-[var(--surface)] px-2 text-sm"
            onChange={(event) => setRunId(event.target.value)}
            value={runId}
          >
            <option value="">选择真实执行记录</option>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>
                {run.status} ·{" "}
                {new Date(run.created_at).toLocaleString("zh-CN")}
              </option>
            ))}
          </select>
          <Button
            disabled={!runId}
            onClick={() => onEvaluate(runId)}
            variant="ghost"
          >
            评估
          </Button>
          <Tooltip content="删除门禁">
            <Button
              aria-label={`删除门禁 ${gate.name}`}
              onClick={onDelete}
              variant="ghost"
            >
              <Trash2 className="size-4 text-[var(--danger)]" />
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
      description={`通过率 ≥ ${(gate.success_rate_threshold * 100).toFixed(0)}%`}
      footer={
        <>
          <ListCardMeta
            items={[
              `安全评分 ≥ ${gate.security_threshold.toFixed(1)}`,
              gate.cost_limit != null ? `成本 ≤ ${gate.cost_limit}` : undefined,
              gate.critical_cases.length > 0
                ? `关键用例 ${gate.critical_cases.length} 个`
                : undefined,
            ]}
          />
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
        <DialogDescription>配置发布前必须满足的条件。</DialogDescription>
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
