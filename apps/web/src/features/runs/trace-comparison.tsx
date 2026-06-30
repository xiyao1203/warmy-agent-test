"use client";

import type { TraceSpan } from "./trace-timeline";

export interface TraceComparisonProps {
  /** 版本 A 的 Spans */
  spansA: TraceSpan[];
  /** 版本 B 的 Spans */
  spansB: TraceSpan[];
  /** 版本 A 标签 */
  labelA?: string;
  /** 版本 B 标签 */
  labelB?: string;
}

interface SpanDiff {
  name: string;
  durationA: number | null;
  durationB: number | null;
  diff: number | null;
  status: "added" | "removed" | "changed" | "unchanged";
}

/**
 * 版本轨迹对比组件。
 *
 * 功能：
 * - 对比两个版本的 Trace
 * - 高亮显示差异
 * - 支持逐 Span 对比
 */
export function TraceComparison({
  spansA,
  spansB,
  labelA = "版本 A",
  labelB = "版本 B",
}: TraceComparisonProps) {
  // 构建 Span 映射
  const mapA = new Map(spansA.map((s) => [s.name, s]));
  const mapB = new Map(spansB.map((s) => [s.name, s]));

  // 合并所有 Span 名称
  const allNames = new Set([...mapA.keys(), ...mapB.keys()]);

  // 计算差异
  const diffs: SpanDiff[] = Array.from(allNames).map((name) => {
    const spanA = mapA.get(name);
    const spanB = mapB.get(name);

    if (!spanA && spanB) {
      return {
        name,
        durationA: null,
        durationB: spanB.duration,
        diff: null,
        status: "added",
      };
    }

    if (spanA && !spanB) {
      return {
        name,
        durationA: spanA.duration,
        durationB: null,
        diff: null,
        status: "removed",
      };
    }

    if (spanA && spanB) {
      const diff = spanB.duration - spanA.duration;
      return {
        name,
        durationA: spanA.duration,
        durationB: spanB.duration,
        diff,
        status: diff === 0 ? "unchanged" : "changed",
      };
    }

    return {
      name,
      durationA: null,
      durationB: null,
      diff: null,
      status: "unchanged",
    };
  });

  const getStatusColor = (status: SpanDiff["status"]) => {
    switch (status) {
      case "added":
        return "text-[var(--success)]";
      case "removed":
        return "text-[var(--danger)]";
      case "changed":
        return "text-[var(--warning)]";
      default:
        return "text-[var(--text)]";
    }
  };

  const getDiffText = (diff: SpanDiff) => {
    if (diff.diff === null) return "";
    if (diff.diff > 0) return `+${diff.diff}ms`;
    if (diff.diff < 0) return `${diff.diff}ms`;
    return "无变化";
  };

  return (
    <div className="space-y-4">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">版本轨迹对比</h3>
        <div className="flex gap-4 text-xs text-[var(--text-muted)]">
          <span>{labelA}</span>
          <span>{labelB}</span>
        </div>
      </div>

      {/* 对比表格 */}
      <div className="overflow-hidden rounded border border-[var(--border)]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[var(--surface-subtle)]">
              <th className="px-4 py-2 text-left font-medium">Span 名称</th>
              <th className="px-4 py-2 text-right font-medium">{labelA}</th>
              <th className="px-4 py-2 text-right font-medium">{labelB}</th>
              <th className="px-4 py-2 text-right font-medium">差异</th>
            </tr>
          </thead>
          <tbody>
            {diffs.map((diff) => (
              <tr
                key={diff.name}
                className={`border-b border-[var(--border)] last:border-0 ${
                  diff.status === "changed" ? "bg-[var(--warning-subtle)]" : ""
                }`}
              >
                <td className="px-4 py-2">
                  <span className={getStatusColor(diff.status)}>
                    {diff.name}
                  </span>
                </td>
                <td className="px-4 py-2 text-right font-mono">
                  {diff.durationA !== null ? `${diff.durationA}ms` : "-"}
                </td>
                <td className="px-4 py-2 text-right font-mono">
                  {diff.durationB !== null ? `${diff.durationB}ms` : "-"}
                </td>
                <td
                  className={`px-4 py-2 text-right font-mono ${getStatusColor(diff.status)}`}
                >
                  {getDiffText(diff)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 统计摘要 */}
      <div className="flex gap-4 text-xs text-[var(--text-muted)]">
        <span>新增: {diffs.filter((d) => d.status === "added").length}</span>
        <span>移除: {diffs.filter((d) => d.status === "removed").length}</span>
        <span>变化: {diffs.filter((d) => d.status === "changed").length}</span>
        <span>
          不变: {diffs.filter((d) => d.status === "unchanged").length}
        </span>
      </div>
    </div>
  );
}
