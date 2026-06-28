"use client";

import { AlertTriangle, Clock, DollarSign, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";

export interface CostEstimate {
  /** 用例数量 */
  caseCount: number;
  /** 单次执行成本（美元） */
  costPerCase: number;
  /** 估算 Token 消耗 */
  estimatedTokens: number;
  /** 预计执行时间（秒） */
  estimatedDuration: number;
}

export interface CostEstimateCardProps {
  /** 成本估算数据 */
  estimate: CostEstimate;
  /** 成本阈值（超过时显示警告） */
  costThreshold?: number;
  /** 确认回调 */
  onConfirm?: () => void;
  /** 取消回调 */
  onCancel?: () => void;
}

/**
 * 成本估算卡片组件。
 *
 * 功能：
 * - 计算用例数 × 单次成本
 * - 估算 Token 消耗
 * - 展示预计执行时间
 * - 超过阈值时请求确认
 */
export function CostEstimateCard({
  estimate,
  costThreshold = 100,
  onConfirm,
  onCancel,
}: CostEstimateCardProps) {
  const totalCost = estimate.caseCount * estimate.costPerCase;
  const isOverThreshold = totalCost > costThreshold;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("zh-CN", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds} 秒`;
    if (seconds < 3600) return `${Math.round(seconds / 60)} 分钟`;
    return `${(seconds / 3600).toFixed(1)} 小时`;
  };

  const formatTokens = (tokens: number) => {
    if (tokens < 1000) return `${tokens}`;
    if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}K`;
    return `${(tokens / 1000000).toFixed(1)}M`;
  };

  return (
    <div className="space-y-4 rounded border border-[var(--border)] p-4">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">成本估算</h3>
        {isOverThreshold && (
          <Badge tone="warning">
            <AlertTriangle className="mr-1 size-3" />
            超出预算
          </Badge>
        )}
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded border border-[var(--border)] p-3">
          <div className="flex items-center gap-2 text-[var(--text-muted)]">
            <DollarSign className="size-4" />
            <span className="text-xs">总成本</span>
          </div>
          <p className={`mt-1 text-lg font-semibold ${
            isOverThreshold ? "text-[var(--danger)]" : ""
          }`}>
            {formatCurrency(totalCost)}
          </p>
        </div>

        <div className="rounded border border-[var(--border)] p-3">
          <div className="flex items-center gap-2 text-[var(--text-muted)]">
            <Zap className="size-4" />
            <span className="text-xs">Token 消耗</span>
          </div>
          <p className="mt-1 text-lg font-semibold">
            {formatTokens(estimate.estimatedTokens)}
          </p>
        </div>

        <div className="rounded border border-[var(--border)] p-3">
          <div className="flex items-center gap-2 text-[var(--text-muted)]">
            <Clock className="size-4" />
            <span className="text-xs">预计时间</span>
          </div>
          <p className="mt-1 text-lg font-semibold">
            {formatDuration(estimate.estimatedDuration)}
          </p>
        </div>

        <div className="rounded border border-[var(--border)] p-3">
          <div className="flex items-center gap-2 text-[var(--text-muted)]">
            <span className="text-xs">用例数</span>
          </div>
          <p className="mt-1 text-lg font-semibold">
            {estimate.caseCount}
          </p>
        </div>
      </div>

      {/* 警告提示 */}
      {isOverThreshold && (
        <div className="rounded bg-[var(--warning-subtle)] p-3">
          <p className="text-sm text-[var(--warning)]">
            预计成本 {formatCurrency(totalCost)} 已超过阈值 {formatCurrency(costThreshold)}，是否继续执行？
          </p>
        </div>
      )}

      {/* 操作按钮 */}
      {(onConfirm || onCancel) && (
        <div className="flex gap-2">
          {onConfirm && (
            <button
              className="flex-1 rounded bg-[var(--accent)] px-4 py-2 text-sm text-white"
              onClick={onConfirm}
            >
              确认执行
            </button>
          )}
          {onCancel && (
            <button
              className="flex-1 rounded border border-[var(--border)] px-4 py-2 text-sm"
              onClick={onCancel}
            >
              取消
            </button>
          )}
        </div>
      )}
    </div>
  );
}
