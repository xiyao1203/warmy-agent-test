"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import type { ScorerItem } from "./api";
import { createScorer, trialScorer, updateScorer } from "./api";

export function ScorerEditorDialog({
  onOpenChange,
  onSaved,
  open,
  projectId,
  scorer,
}: {
  onOpenChange: (open: boolean) => void;
  onSaved: () => Promise<unknown>;
  open: boolean;
  projectId: string;
  scorer?: ScorerItem;
}) {
  const isEdit = Boolean(scorer);
  const [name, setName] = useState(scorer?.name ?? "");
  const [scorerType, setScorerType] = useState(scorer?.scorer_type ?? "rule");
  const [weight, setWeight] = useState(scorer?.weight ?? 1.0);
  const [threshold, setThreshold] = useState(scorer?.threshold ?? 0.8);
  const [description, setDescription] = useState(scorer?.description ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [operator, setOperator] = useState(
    String(scorer?.config_json.operator ?? "contains"),
  );
  const [expected, setExpected] = useState(
    String(scorer?.config_json.expected ?? ""),
  );
  const [rubric, setRubric] = useState(
    String(scorer?.config_json.rubric ?? ""),
  );
  const [sampleOutput, setSampleOutput] = useState("");
  const [sampleReference, setSampleReference] = useState("");
  const [trialResult, setTrialResult] = useState<string>("");

  function scorerConfig() {
    if (scorerType === "model") return { rubric };
    if (scorerType === "reference") return { operator };
    return { expected, operator };
  }

  async function handleSave() {
    if (!name.trim()) {
      setError("名称不能为空");
      return;
    }
    setSaving(true);
    setError("");
    try {
      if (isEdit && scorer) {
        await updateScorer(projectId, scorer.id, {
          name: name.trim(),
          weight,
          threshold,
          description: description || null,
          config_json: scorerConfig(),
        });
      } else {
        await createScorer(projectId, {
          name: name.trim(),
          scorer_type: scorerType,
          weight,
          threshold,
          description: description || null,
          config_json: scorerConfig(),
        });
      }
      onOpenChange(false);
      await onSaved();
    } catch {
      setError("保存失败，请重试。");
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
        <DialogTitle>{isEdit ? "编辑评分器" : "创建评分器"}</DialogTitle>
        <DialogDescription>
          配置评分器的类型、权重和通过阈值。
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
          <label className="block text-sm font-medium">
            类型
            <select
              className="mt-1.5 h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
              disabled={isEdit}
              onChange={(e) => setScorerType(e.target.value)}
              value={scorerType}
            >
              <option value="rule">规则（Rule）</option>
              <option value="model">模型（Model）</option>
              <option value="reference">参考（Reference）</option>
            </select>
            <span className="mt-1 block text-xs text-[var(--muted)]">
              {scorerType === "rule"
                ? "基于固定规则比较输出与期望值"
                : scorerType === "model"
                  ? "通过模型按评分标准（Rubric）评估输出质量"
                  : "比较输出与参考答案的一致性"}
            </span>
          </label>
          <div className="grid grid-cols-2 gap-4">
            <label className="block text-sm font-medium">
              权重
              <Input
                className="mt-1.5"
                max={10}
                min={0}
                onChange={(e) => setWeight(Number(e.target.value))}
                step={0.1}
                type="number"
                value={weight}
              />
              <span className="mt-1 block text-xs text-[var(--muted)]">
                多评分器加权时的相对权重（0-10）
              </span>
            </label>
            <label className="block text-sm font-medium">
              通过阈值
              <Input
                className="mt-1.5"
                max={1}
                min={0}
                onChange={(e) => setThreshold(Number(e.target.value))}
                step={0.01}
                type="number"
                value={threshold}
              />
              <span className="mt-1 block text-xs text-[var(--muted)]">
                分数 ≥ 此值视为通过（0.00-1.00）
              </span>
            </label>
          </div>
          {scorerType === "model" ? (
            <label className="block text-sm font-medium">
              评分标准（Rubric）
              <textarea
                className="mt-1.5 min-h-24 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] p-3 text-sm"
                onChange={(event) => setRubric(event.target.value)}
                placeholder="明确描述 0-1 分的判断标准"
                value={rubric}
              />
              <span className="mt-1 block text-xs text-[var(--muted)]">
                模型将严格按此标准打分，建议明确写出各分数段的条件
              </span>
            </label>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <label className="block text-sm font-medium">
                比较方式
                <select
                  className="mt-1.5 h-9 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] px-3"
                  onChange={(event) => setOperator(event.target.value)}
                  value={operator}
                >
                  <option value="contains">包含</option>
                  <option value="exact">完全相等</option>
                </select>
                <span className="mt-1 block text-xs text-[var(--muted)]">
                  {scorerType === "rule"
                    ? "输出是否包含/等于期望值"
                    : "输出是否包含/等于参考答案"}
                </span>
              </label>
              {scorerType === "rule" && (
                <label className="block text-sm font-medium">
                  期望值
                  <Input
                    className="mt-1.5"
                    onChange={(event) => setExpected(event.target.value)}
                    value={expected}
                  />
                  <span className="mt-1 block text-xs text-[var(--muted)]">
                    期望在输出中找到的值
                  </span>
                </label>
              )}
            </div>
          )}
          <label className="block text-sm font-medium">
            描述（可选）
            <Input
              className="mt-1.5"
              onChange={(e) => setDescription(e.target.value)}
              placeholder="评分器的用途说明"
              value={description}
            />
          </label>
          {scorer && (
            <div className="rounded border border-[var(--hairline)] p-3">
              <p className="text-sm font-medium">真实试评</p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                输入样例数据验证评分器是否按预期工作。
              </p>
              <Input
                className="mt-2"
                onChange={(event) => setSampleOutput(event.target.value)}
                placeholder="样例输出（必填）"
                value={sampleOutput}
              />
              {scorerType === "reference" && (
                <Input
                  className="mt-2"
                  onChange={(event) => setSampleReference(event.target.value)}
                  placeholder="参考答案"
                  value={sampleReference}
                />
              )}
              <Button
                className="mt-2"
                onClick={async () => {
                  try {
                    const result = await trialScorer(projectId, scorer.id, {
                      output: sampleOutput,
                      reference: sampleReference || undefined,
                    });
                    setTrialResult(
                      `${result.passed ? "通过" : "未通过"} · ${result.score.toFixed(2)} · ${result.explanation}`,
                    );
                  } catch {
                    setTrialResult("试评失败，请检查配置及模型运行时。");
                  }
                }}
                type="button"
              >
                运行试评
              </Button>
              {trialResult ? (
                <p
                  className={`mt-2 rounded px-2 py-1 text-xs ${trialResult.startsWith("通过") ? "bg-[var(--success-subtle)] text-[var(--success)]" : trialResult.startsWith("未通过") ? "bg-[var(--warning-subtle)] text-[var(--warning)]" : "bg-[var(--danger-subtle)] text-[var(--danger)]"}`}
                >
                  {trialResult}
                </p>
              ) : null}
            </div>
          )}
        </div>
        {error ? (
          <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>
        ) : null}
        <div className="mt-5 flex justify-end gap-2">
          <Button onClick={() => onOpenChange(false)}>取消</Button>
          <Button
            disabled={saving}
            loading={saving}
            onClick={handleSave}
            variant="primary"
          >
            {isEdit ? "保存" : "创建"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
