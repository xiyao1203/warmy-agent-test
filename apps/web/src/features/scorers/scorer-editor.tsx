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
import { createScorer, updateScorer } from "./api";

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
        });
      } else {
        await createScorer(projectId, {
          name: name.trim(),
          scorer_type: scorerType,
          weight,
          threshold,
          description: description || null,
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
              className="mt-1.5 h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3"
              disabled={isEdit}
              onChange={(e) => setScorerType(e.target.value)}
              value={scorerType}
            >
              <option value="rule">规则（Rule）</option>
              <option value="model">模型（Model）</option>
              <option value="reference">参考（Reference）</option>
            </select>
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
            </label>
          </div>
          <label className="block text-sm font-medium">
            描述（可选）
            <Input
              className="mt-1.5"
              onChange={(e) => setDescription(e.target.value)}
              placeholder="评分器的用途说明"
              value={description}
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
