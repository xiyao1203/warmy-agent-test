"use client";

import { Badge } from "@/components/ui/badge";

type Degradation = {
  case_id: string;
  metric: string;
  baseline: number | string;
  current: number | string;
  change: number;
};

type DegradationHighlightProps = {
  degradations: Degradation[];
};

export function DegradationHighlight({
  degradations,
}: DegradationHighlightProps) {
  if (degradations.length === 0) {
    return (
      <div className="rounded-[var(--radius-md)] border border-dashed border-[var(--border)] p-4 text-center">
        <p className="text-sm text-[var(--text-muted)]">无退化项</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {degradations.map((deg) => (
        <div
          key={`${deg.case_id}-${deg.metric}`}
          className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--danger)] bg-[var(--danger-subtle)] p-3"
        >
          <div className="flex items-center gap-3">
            <span className="font-medium">{deg.case_id}</span>
            <Badge tone="danger">{deg.metric}</Badge>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-[var(--text-muted)]">
              {typeof deg.baseline === "number"
                ? deg.baseline.toFixed(2)
                : deg.baseline}
            </span>
            <span>→</span>
            <span className="font-medium text-[var(--danger)]">
              {typeof deg.current === "number"
                ? deg.current.toFixed(2)
                : deg.current}
            </span>
            <span className="text-[var(--danger)]">
              {deg.change > 0 ? "+" : ""}
              {(deg.change * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
