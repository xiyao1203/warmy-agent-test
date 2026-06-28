"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface RubricDimension {
  id: string;
  name: string;
  description: string;
  score: number;
  comment: string;
}

export interface RubricEditorProps {
  /** 评分维度列表 */
  dimensions: RubricDimension[];
  /** 维度变更回调 */
  onDimensionsChange: (dimensions: RubricDimension[]) => void;
  /** 是否禁用 */
  disabled?: boolean;
  /** 最小分数 */
  minScore?: number;
  /** 最大分数 */
  maxScore?: number;
}

/**
 * Rubric 多维评分编辑器。
 *
 * 支持配置多个评分维度（质量、准确性、安全性等），
 * 每个维度支持 1-5 分评分和评分说明。
 */
export function RubricEditor({
  dimensions,
  onDimensionsChange,
  disabled = false,
  minScore = 1,
  maxScore = 5,
}: RubricEditorProps) {
  const handleScoreChange = (dimensionId: string, score: number) => {
    const clampedScore = Math.min(Math.max(score, minScore), maxScore);
    onDimensionsChange(
      dimensions.map((d) =>
        d.id === dimensionId ? { ...d, score: clampedScore } : d,
      ),
    );
  };

  const handleCommentChange = (dimensionId: string, comment: string) => {
    onDimensionsChange(
      dimensions.map((d) =>
        d.id === dimensionId ? { ...d, comment } : d,
      ),
    );
  };

  const totalScore = dimensions.reduce((sum, d) => sum + d.score, 0);
  const maxTotal = dimensions.length * maxScore;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">多维评分</h3>
        <span className="text-sm text-[var(--text-muted)]">
          {totalScore} / {maxTotal}
        </span>
      </div>

      {dimensions.length === 0 ? (
        <p className="text-sm text-[var(--text-muted)]">暂无评分维度</p>
      ) : (
        <div className="space-y-3">
          {dimensions.map((dimension) => (
            <div
              key={dimension.id}
              className="rounded border border-[var(--border)] p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{dimension.name}</p>
                  {dimension.description ? (
                    <p className="mt-1 text-xs text-[var(--text-muted)]">
                      {dimension.description}
                    </p>
                  ) : null}
                </div>

                {/* 分数输入 */}
                <div className="flex items-center gap-2">
                  <label className="text-xs text-[var(--text-muted)]">
                    分数
                  </label>
                  <Input
                    className="w-16 text-center"
                    disabled={disabled}
                    max={maxScore}
                    min={minScore}
                    onChange={(e) =>
                      handleScoreChange(dimension.id, Number(e.target.value))
                    }
                    type="number"
                    value={dimension.score}
                  />
                  <span className="text-xs text-[var(--text-muted)]">
                    / {maxScore}
                  </span>
                </div>
              </div>

              {/* 评分说明 */}
              <div className="mt-2">
                <Input
                  className="text-sm"
                  disabled={disabled}
                  onChange={(e) =>
                    handleCommentChange(dimension.id, e.target.value)
                  }
                  placeholder="评分说明（可选）"
                  value={dimension.comment}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Rubric 评分展示组件（只读）。
 */
export function RubricDisplay({
  dimensions,
}: {
  dimensions: RubricDimension[];
}) {
  if (dimensions.length === 0) {
    return null;
  }

  const totalScore = dimensions.reduce((sum, d) => sum + d.score, 0);
  const maxTotal = dimensions.length * 5;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">多维评分</h4>
        <span className="text-sm font-semibold">
          {totalScore} / {maxTotal}
        </span>
      </div>

      {dimensions.map((dimension) => (
        <div
          key={dimension.id}
          className="flex items-center justify-between rounded border border-[var(--border)] px-3 py-2"
        >
          <div>
            <p className="text-sm">{dimension.name}</p>
            {dimension.comment ? (
              <p className="text-xs text-[var(--text-muted)]">
                {dimension.comment}
              </p>
            ) : null}
          </div>
          <span className="text-sm font-semibold">
            {dimension.score} / 5
          </span>
        </div>
      ))}
    </div>
  );
}
