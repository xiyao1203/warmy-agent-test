import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

export type MetricTone =
  | "accent"
  | "danger"
  | "info"
  | "neutral"
  | "success"
  | "warning";

export type MetricState =
  | "default"
  | "empty"
  | "error"
  | "restricted"
  | "running"
  | "selected"
  | "updated"
  | "warning";

type MetricCardProps = Omit<HTMLAttributes<HTMLElement>, "title"> & {
  action?: ReactNode;
  change?: ReactNode;
  disabled?: boolean;
  icon?: ReactNode;
  label: string;
  loading?: boolean;
  meta?: ReactNode;
  state?: MetricState;
  tone?: MetricTone;
  value: ReactNode;
};

export function MetricGrid({
  className,
  columns = 4,
  ...props
}: HTMLAttributes<HTMLDivElement> & { columns?: 3 | 4 }) {
  return (
    <div
      className={cn("precision-metric-grid", className)}
      data-columns={columns}
      {...props}
    />
  );
}

export function MetricCard({
  action,
  change,
  className,
  disabled = false,
  icon,
  label,
  loading = false,
  meta,
  state = "default",
  tone = "neutral",
  value,
  ...props
}: MetricCardProps) {
  if (loading) {
    return <MetricCardSkeleton className={className} label={label} />;
  }

  const interactive = Boolean(action) && !disabled;

  return (
    <article
      aria-label={label}
      className={cn("precision-metric-card", className)}
      data-disabled={disabled || undefined}
      data-interactive={interactive}
      data-state={state}
      data-tone={tone}
      {...props}
    >
      {icon ? (
        <span className="precision-metric-icon" data-metric-icon>
          {icon}
        </span>
      ) : null}
      <div className="precision-metric-copy">
        <div className="precision-metric-label-row">
          <span className="precision-metric-label">{label}</span>
          {meta ? <span className="precision-metric-meta">{meta}</span> : null}
        </div>
        <div className="precision-metric-value-row">
          <strong className="precision-metric-value">{value}</strong>
          {change ? (
            <span className="precision-metric-change">{change}</span>
          ) : null}
        </div>
      </div>
      {action ? <div className="precision-metric-action">{action}</div> : null}
    </article>
  );
}

export function MetricCardSkeleton({
  className,
  label,
}: {
  className?: string;
  label: string;
}) {
  return (
    <article
      aria-busy="true"
      aria-label={label}
      className={cn(
        "precision-metric-card precision-metric-skeleton",
        className,
      )}
    >
      <span className="precision-skeleton-icon" />
      <div className="precision-metric-copy">
        <span className="precision-skeleton-line precision-skeleton-label" />
        <span className="precision-skeleton-line precision-skeleton-value" />
      </div>
    </article>
  );
}
