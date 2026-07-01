"use client";

import { AggregationView } from "./aggregation-view";
import { DegradationHighlight } from "./degradation-highlight";

type MetricStats = {
  avg: number;
  p50: number;
  p95: number;
  std_dev: number;
  min_val: number;
  max_val: number;
};

type Statistics = {
  total_cases: number;
  passed: number;
  failed: number;
  pass_rate: number;
  latency: MetricStats;
  score: MetricStats;
  cost: MetricStats;
};

type Degradation = {
  case_id: string;
  metric: string;
  baseline: number | string;
  current: number | string;
  change: number;
};

type RunData = {
  id: string;
  statistics: Statistics;
};

type ExperimentCompareProps = {
  experimentId: string;
  runA: RunData;
  runB: RunData;
  degradations: Degradation[];
};

export function ExperimentCompare({
  experimentId,
  runA,
  runB,
  degradations,
}: ExperimentCompareProps) {
  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">实验对比</h2>
        <span className="text-sm text-[var(--muted)]">
          ID: {experimentId}
        </span>
      </div>

      {/* 运行对比 */}
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h3 className="mb-3 text-lg font-semibold">
            运行 A: <span className="font-mono text-sm">{runA.id}</span>
          </h3>
          <AggregationView statistics={runA.statistics} />
        </div>
        <div>
          <h3 className="mb-3 text-lg font-semibold">
            运行 B: <span className="font-mono text-sm">{runB.id}</span>
          </h3>
          <AggregationView statistics={runB.statistics} />
        </div>
      </div>

      {/* 退化项 */}
      <div>
        <h3 className="mb-3 text-lg font-semibold">退化项</h3>
        <DegradationHighlight degradations={degradations} />
      </div>
    </div>
  );
}
