"use client";

import { AlertTriangle, DollarSign } from "lucide-react";

export interface BudgetDisplayProps {
  /** 预算总额 */
  budget: number;
  /** 已用金额 */
  used: number;
  /** 剩余金额 */
  remaining?: number;
  /** 使用百分比 */
  usagePercent?: number;
}

/**
 * 成本预算展示组件。
 *
 * 功能：
 * - 展示预算总额、已用、剩余
 * - 进度条显示使用情况
 * - 超过 80% 显示警告
 * - 超过 100% 显示超支提示
 */
export function BudgetDisplay({
  budget,
  used,
  remaining: remainingProp,
  usagePercent: usagePercentProp,
}: BudgetDisplayProps) {
  const remaining = remainingProp ?? budget - used;
  const usagePercent = usagePercentProp ?? (budget > 0 ? (used / budget) * 100 : 0);
  const isWarning = usagePercent >= 80;
  const isExceeded = usagePercent >= 100;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("zh-CN", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="space-y-4">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <DollarSign className="size-5 text-[var(--text-muted)]" />
          <h3 className="text-sm font-medium">成本预算</h3>
        </div>
        <span
          className={`text-sm font-semibold ${
            isExceeded
              ? "text-[var(--danger)]"
              : isWarning
                ? "text-[var(--warning)]"
                : "text-[var(--text)]"
          }`}
        >
          {usagePercent.toFixed(1)}%
        </span>
      </div>

      {/* 金额卡片 */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded border border-[var(--border)] p-3 text-center">
          <p className="text-xs text-[var(--text-muted)]">预算</p>
          <p className="mt-1 text-sm font-semibold">
            {formatCurrency(budget)}
          </p>
        </div>
        <div className="rounded border border-[var(--border)] p-3 text-center">
          <p className="text-xs text-[var(--text-muted)]">已用</p>
          <p className="mt-1 text-sm font-semibold">
            {formatCurrency(used)}
          </p>
        </div>
        <div className="rounded border border-[var(--border)] p-3 text-center">
          <p className="text-xs text-[var(--text-muted)]">剩余</p>
          <p
            className={`mt-1 text-sm font-semibold ${
              isExceeded ? "text-[var(--danger)]" : ""
            }`}
          >
            {formatCurrency(remaining)}
          </p>
        </div>
      </div>

      {/* 进度条 */}
      <div className="space-y-2">
        <div className="h-2 overflow-hidden rounded-full bg-[var(--surface-subtle)]">
          <div
            className={`h-full transition-all ${
              isExceeded
                ? "bg-[var(--danger)]"
                : isWarning
                  ? "bg-[var(--warning)]"
                  : "bg-[var(--accent)]"
            }`}
            style={{ width: `${Math.min(usagePercent, 100)}%` }}
          />
        </div>

        {/* 警告提示 */}
        {isWarning && !isExceeded && (
          <div className="flex items-center gap-2 text-[var(--warning)]">
            <AlertTriangle className="size-4" />
            <span className="text-xs">预算使用已达 80%，请注意控制成本</span>
          </div>
        )}

        {isExceeded && (
          <div className="flex items-center gap-2 text-[var(--danger)]">
            <AlertTriangle className="size-4" />
            <span className="text-xs">预算已超支，建议停止执行</span>
          </div>
        )}
      </div>
    </div>
  );
}
