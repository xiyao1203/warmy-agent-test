import type { HTMLAttributes, ReactNode } from "react";

type StatCardProps = HTMLAttributes<HTMLDivElement> & {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: string;
    positive?: boolean;
  };
};

export function StatCard({
  className = "",
  icon,
  label,
  trend,
  value,
  ...props
}: StatCardProps) {
  return (
    <div
      className={`rounded-[var(--radius)] border border-[var(--hairline)] bg-[var(--surface)] p-6 shadow-sm transition-shadow hover:shadow-md ${className}`}
      {...props}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--muted)]">
            {label}
          </p>
          <p className="mt-1 text-3xl font-bold text-[var(--ink)]">{value}</p>
        </div>
        {icon && (
          <div className="rounded-full bg-[var(--primary-subtle)] p-3 text-[var(--primary)]">
            {icon}
          </div>
        )}
      </div>
      {trend && (
        <div className="mt-4 flex items-center gap-2 text-sm">
          <span
            className={
              trend.positive !== false ? "text-emerald-500" : "text-red-500"
            }
          >
            {trend.positive !== false ? "↑" : "↓"} {trend.value}
          </span>
          <span className="text-[var(--muted)]">vs 上期</span>
        </div>
      )}
    </div>
  );
}
