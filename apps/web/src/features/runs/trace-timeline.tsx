"use client";

export interface TraceSpan {
  id: string;
  name: string;
  startTime: number;
  duration: number;
  status: "ok" | "error" | "timeout";
  parentId?: string;
  attributes?: Record<string, string>;
  children: TraceSpan[];
}

export interface TraceTimelineProps {
  /** Trace Span 列表 */
  spans: TraceSpan[];
  /** Span 点击回调 */
  onSpanClick?: (span: TraceSpan) => void;
}

/**
 * Trace 时间轴展示组件。
 *
 * 功能：
 * - 时间轴展示 Trace 执行顺序
 * - 高亮显示错误 Span
 * - 支持点击查看 Span 详情
 */
export function TraceTimeline({ spans, onSpanClick }: TraceTimelineProps) {
  if (spans.length === 0) {
    return (
      <div className="flex min-h-[200px] items-center justify-center rounded border border-dashed border-[var(--hairline)]">
        <p className="text-sm text-[var(--muted)]">暂无 Trace 数据</p>
      </div>
    );
  }

  // 计算总时长
  const maxEndTime = Math.max(...spans.map((s) => s.startTime + s.duration));
  const totalDuration = maxEndTime;

  return (
    <div className="space-y-4">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Trace 时间轴</h3>
        <span className="text-xs text-[var(--muted)]">
          总耗时: {totalDuration}ms
        </span>
      </div>

      {/* 时间刻度 */}
      <div className="flex justify-between text-xs text-[var(--muted)]">
        <span>0ms</span>
        <span>{Math.round(totalDuration / 4)}ms</span>
        <span>{Math.round(totalDuration / 2)}ms</span>
        <span>{Math.round((totalDuration * 3) / 4)}ms</span>
        <span>{totalDuration}ms</span>
      </div>

      {/* Span 列表 */}
      <div className="space-y-2">
        {spans.map((span) => {
          const isError = span.status === "error";
          const leftPercent = (span.startTime / totalDuration) * 100;
          const widthPercent = (span.duration / totalDuration) * 100;

          return (
            <div
              key={span.id}
              className={`cursor-pointer rounded border p-3 transition-colors ${
                isError
                  ? "border-[var(--danger)] bg-[var(--danger-subtle)]"
                  : "border-[var(--hairline)] hover:bg-[var(--canvas-soft)]"
              }`}
              onClick={() => onSpanClick?.(span)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{span.name}</span>
                  {isError && (
                    <span className="rounded bg-[var(--danger)] px-1.5 py-0.5 text-xs text-[var(--on-primary)]">
                      错误
                    </span>
                  )}
                </div>
                <span className="text-xs text-[var(--muted)]">
                  {span.duration}ms
                </span>
              </div>

              {/* 时间条 */}
              <div className="relative mt-2 h-2 overflow-hidden rounded-full bg-[var(--canvas-soft)]">
                <div
                  className={`absolute h-full rounded-full ${
                    isError ? "bg-[var(--danger)]" : "bg-[var(--primary)]"
                  }`}
                  style={{
                    left: `${leftPercent}%`,
                    width: `${widthPercent}%`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
