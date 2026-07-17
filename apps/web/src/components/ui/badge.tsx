import type { HTMLAttributes } from "react";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: "accent" | "danger" | "neutral" | "success" | "warning";
};

export function Badge({
  className = "",
  tone = "neutral",
  ...props
}: BadgeProps) {
  const tones: Record<string, string> = {
    accent: "bg-[var(--primary-subtle)] text-[var(--primary)]",
    danger: "bg-[var(--danger-subtle)] text-[var(--danger)]",
    neutral:
      "border border-[var(--hairline)] bg-[var(--canvas-soft)] text-[var(--body)]",
    success: "bg-[var(--success-subtle)] text-[var(--success)]",
    warning: "bg-[var(--warning-subtle)] text-[var(--warning)]",
  };

  return (
    <span
      className={`inline-flex items-center rounded-[var(--radius-pill)] px-2 py-0.5 text-[11px] font-medium tracking-[0.02em] ${tones[tone]} ${className}`}
      {...props}
    />
  );
}
