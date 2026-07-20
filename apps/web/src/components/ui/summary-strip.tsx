import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

import {
  MetricCard,
  MetricGrid,
  type MetricState,
  type MetricTone,
} from "./metric-card";

export function SummaryStrip({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <MetricGrid className={cn("my-4", className)} {...props} />;
}

export function SummaryItem({
  icon,
  label,
  state,
  tone,
  value,
}: {
  icon?: ReactNode;
  label: string;
  state?: MetricState;
  tone?: MetricTone;
  value: ReactNode;
}) {
  return (
    <MetricCard
      icon={icon}
      label={label}
      state={state}
      tone={tone}
      value={value}
    />
  );
}
