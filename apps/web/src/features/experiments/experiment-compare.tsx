"use client";

import Link from "next/link";

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
  projectId?: string;
  runA: RunData;
  runB: RunData;
  degradations: Degradation[];
};

export function ExperimentCompare({
  experimentId,
  projectId,
  runA,
  runB,
  degradations,
}: ExperimentCompareProps) {
  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">实验对比结果</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            对照两次运行的通过率、评分、耗时和退化项。
          </p>
        </div>
        <div className="flex items-center gap-3">
          {projectId ? (
            <>
              <Link
                className="text-sm font-medium text-[var(--primary)] hover:underline"
                href={`/projects/${projectId}/runs`}
              >
                查看运行结果
              </Link>
              <Link
                className="text-sm font-medium text-[var(--primary)] hover:underline"
                href={`/projects/${projectId}/gates`}
              >
                配置发布门禁
              </Link>
            </>
          ) : null}
          <span className="text-sm text-[var(--muted)]">
            ID: {experimentId}
          </span>
        </div>
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
