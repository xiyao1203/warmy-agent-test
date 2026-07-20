import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

export function SummaryStrip({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "grid border-b border-[var(--hairline)] py-4 text-sm [grid-template-columns:repeat(auto-fit,minmax(8rem,1fr))]",
        className,
      )}
      {...props}
    />
  );
}

export function SummaryItem({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="border-r border-[var(--hairline)] px-4 first:pl-0 last:border-r-0">
      <p className="text-xs text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-lg font-semibold text-[var(--ink)]">{value}</p>
    </div>
  );
}
