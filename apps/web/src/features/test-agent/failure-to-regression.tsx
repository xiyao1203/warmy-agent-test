"use client";

import { useState } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";

export interface FailureCase {
  /** 失败用例 ID */
  id: string;
  /** 失败原因 */
  reason: string;
  /** 输入内容 */
  input: string;
  /** 预期输出 */
  expectedOutput: string;
  /** 实际输出 */
  actualOutput: string;
}

export interface FailureToRegressionProps {
  /** 失败用例列表 */
  failures: FailureCase[];
  /** 转换回调 */
  onConvert?: (caseIds: string[]) => void;
}

/**
 * 失败→回归转换组件。
 *
 * 功能：
 * - 一键转换失败用例为回归用例
 * - 自动填充输入和预期输出
 * - 支持批量转换
 */
export function FailureToRegression({
  failures,
  onConvert,
}: FailureToRegressionProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : [...prev, id],
    );
  };

  const selectAll = () => {
    setSelectedIds(failures.map((f) => f.id));
  };

  const deselectAll = () => {
    setSelectedIds([]);
  };

  const handleConvert = () => {
    if (selectedIds.length > 0) {
      onConvert?.(selectedIds);
    }
  };

  return (
    <div className="space-y-4 rounded border border-[var(--border)] p-4">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium">失败用例转换</h3>
          <Badge>{failures.length} 项</Badge>
        </div>
        <div className="flex gap-2">
          <button
            className="text-xs text-[var(--text-muted)] hover:text-[var(--text)]"
            onClick={selectAll}
          >
            全选
          </button>
          <button
            className="text-xs text-[var(--text-muted)] hover:text-[var(--text)]"
            onClick={deselectAll}
          >
            取消全选
          </button>
        </div>
      </div>

      {/* 失败列表 */}
      <div className="max-h-60 space-y-2 overflow-y-auto">
        {failures.map((failure) => (
          <label
            key={failure.id}
            className="flex cursor-pointer items-start gap-3 rounded border border-[var(--border)] p-3 hover:bg-[var(--bg-secondary)]"
          >
            <input
              type="checkbox"
              checked={selectedIds.includes(failure.id)}
              onChange={() => toggleSelect(failure.id)}
              className="mt-1"
            />
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">{failure.id}</span>
                <Badge tone="danger">
                  <AlertTriangle className="mr-1 size-3" />
                  失败
                </Badge>
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                {failure.reason}
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[var(--text-muted)]">输入：</span>
                  <p className="mt-1 rounded bg-[var(--bg-secondary)] p-2">
                    {failure.input.slice(0, 50)}...
                  </p>
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">预期：</span>
                  <p className="mt-1 rounded bg-[var(--bg-secondary)] p-2">
                    {failure.expectedOutput.slice(0, 50)}...
                  </p>
                </div>
              </div>
            </div>
          </label>
        ))}
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-[var(--text-muted)]">
          已选 {selectedIds.length} 项
        </span>
        <button
          className="flex items-center gap-2 rounded bg-[var(--accent)] px-4 py-2 text-sm text-white disabled:opacity-50"
          disabled={selectedIds.length === 0}
          onClick={handleConvert}
        >
          <RefreshCw className="size-4" />
          转换为回归用例
        </button>
      </div>
    </div>
  );
}
