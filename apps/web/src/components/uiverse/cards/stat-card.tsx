import type { HTMLAttributes, ReactNode } from "react";

import { MetricCard } from "@/components/ui/metric-card";

type StatCardProps = HTMLAttributes<HTMLElement> & {
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
    <MetricCard
      change={
        trend
          ? `${trend.positive === false ? "↓" : "↑"} ${trend.value}`
          : undefined
      }
      className={className}
      icon={icon}
      label={label}
      state={trend ? "updated" : "default"}
      tone={
        trend?.positive === false ? "danger" : trend ? "success" : "neutral"
      }
      value={value}
      {...props}
    />
  );
}
