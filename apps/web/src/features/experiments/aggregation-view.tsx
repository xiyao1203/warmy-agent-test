"use client";

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

type AggregationViewProps = {
  statistics: Statistics;
};

export function AggregationView({ statistics }: AggregationViewProps) {
  const { total_cases, passed, failed, pass_rate, latency, score, cost } =
    statistics;

  return (
    <div className="space-y-4">
      {/* 状态统计卡片 */}
      <div className="grid grid-cols-4 gap-2">
        <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-3 text-center">
          <p className="text-xs text-[var(--text-muted)]">总计</p>
          <p className="text-2xl font-bold">{total_cases}</p>
        </div>
        <div className="rounded-[var(--radius-md)] border border-[var(--success)] bg-[var(--success-subtle)] p-3 text-center">
          <p className="text-xs text-[var(--text-muted)]">通过</p>
          <p className="text-2xl font-bold text-[var(--success)]">{passed}</p>
        </div>
        <div className="rounded-[var(--radius-md)] border border-[var(--danger)] bg-[var(--danger-subtle)] p-3 text-center">
          <p className="text-xs text-[var(--text-muted)]">失败</p>
          <p className="text-2xl font-bold text-[var(--danger)]">{failed}</p>
        </div>
        <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-3 text-center">
          <p className="text-xs text-[var(--text-muted)]">通过率</p>
          <p className="text-2xl font-bold">{(pass_rate * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* 延迟统计 */}
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4">
        <h4 className="mb-2 font-medium">延迟 (ms)</h4>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-[var(--text-muted)]">P50</p>
            <p className="text-lg font-semibold">{latency.p50.toFixed(0)}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)]">P95</p>
            <p className="text-lg font-semibold">{latency.p95.toFixed(0)}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)]">平均</p>
            <p className="text-lg font-semibold">{latency.avg.toFixed(0)}</p>
          </div>
        </div>
      </div>

      {/* 分数统计 */}
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4">
        <h4 className="mb-2 font-medium">分数</h4>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-[var(--text-muted)]">P50</p>
            <p className="text-lg font-semibold">{score.p50.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)]">P95</p>
            <p className="text-lg font-semibold">{score.p95.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)]">平均</p>
            <p className="text-lg font-semibold">{score.avg.toFixed(2)}</p>
          </div>
        </div>
      </div>

      {/* 成本统计 */}
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4">
        <h4 className="mb-2 font-medium">成本</h4>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-[var(--text-muted)]">P50</p>
            <p className="text-lg font-semibold">${cost.p50.toFixed(3)}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)]">P95</p>
            <p className="text-lg font-semibold">${cost.p95.toFixed(3)}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)]">平均</p>
            <p className="text-lg font-semibold">${cost.avg.toFixed(3)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
