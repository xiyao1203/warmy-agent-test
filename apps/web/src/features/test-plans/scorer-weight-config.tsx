"use client";

import { AlertTriangle } from "lucide-react";

import { Input } from "@/components/ui/input";

export interface ScorerWeight {
  id: string;
  name: string;
  weight: number;
}

export interface ScorerWeightConfigProps {
  /** 评分器权重列表 */
  scorers: ScorerWeight[];
  /** 权重变更回调 */
  onChange: (scorers: ScorerWeight[]) => void;
  /** 是否禁用 */
  disabled?: boolean;
}

/**
 * 评分器权重配置组件。
 *
 * 支持：
 * - 添加多个评分器
 * - 每个评分器设置权重（0-100%）
 * - 权重总和自动校验
 */
export function ScorerWeightConfig({
  scorers,
  onChange,
  disabled = false,
}: ScorerWeightConfigProps) {
  const totalWeight = scorers.reduce((sum, s) => sum + s.weight, 0);
  const isValid = totalWeight === 100;

  const handleWeightChange = (scorerId: string, weight: number) => {
    const clampedWeight = Math.min(Math.max(weight, 0), 100);
    onChange(
      scorers.map((s) =>
        s.id === scorerId ? { ...s, weight: clampedWeight } : s,
      ),
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">评分器权重配置</h3>
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-semibold ${
              isValid ? "text-[var(--success)]" : "text-[var(--danger)]"
            }`}
          >
            {totalWeight}%
          </span>
          {!isValid && (
            <div className="flex items-center gap-1 text-[var(--warning)]">
              <AlertTriangle className="size-4" />
              <span className="text-xs">权重总和应为 100%</span>
            </div>
          )}
        </div>
      </div>

      {scorers.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">暂无评分器</p>
      ) : (
        <div className="space-y-3">
          {scorers.map((scorer, index) => (
            <div
              key={scorer.id}
              className="flex items-center gap-4 rounded border border-[var(--hairline)] p-3"
            >
              <div className="flex size-8 items-center justify-center rounded-full bg-[var(--canvas-soft)] text-sm font-medium">
                {index + 1}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{scorer.name}</p>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-[var(--muted)]">权重</label>
                <Input
                  className="w-20 text-center"
                  disabled={disabled}
                  max={100}
                  min={0}
                  onChange={(e) =>
                    handleWeightChange(scorer.id, Number(e.target.value))
                  }
                  type="number"
                  value={scorer.weight}
                />
                <span className="text-xs text-[var(--muted)]">%</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 权重分布条 */}
      {scorers.length > 0 && (
        <div className="h-2 overflow-hidden rounded-full bg-[var(--canvas-soft)]">
          <div
            className="h-full bg-[var(--primary)] transition-all"
            style={{ width: `${totalWeight}%` }}
          />
        </div>
      )}
    </div>
  );
}
