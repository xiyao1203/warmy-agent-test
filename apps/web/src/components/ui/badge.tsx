import type { HTMLAttributes } from "react";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: "accent" | "danger" | "neutral" | "success" | "warning";
};

export function Badge({
  className = "",
  tone = "neutral",
  ...props
}: BadgeProps) {
  const tones = {
    accent: "bg-[var(--accent-subtle)] text-[var(--accent-text)]",
    danger: "bg-[var(--danger-subtle)] text-[var(--danger)]",
    neutral: "bg-[var(--surface-subtle)] text-[var(--text-muted)]",
    success: "bg-[var(--success-subtle)] text-[var(--success)]",
    warning: "bg-[var(--warning-subtle)] text-[var(--warning)]",
  };

  return (
    <span
      className={`inline-flex min-h-5 items-center rounded-[var(--radius-sm)] px-1.5 text-xs font-medium ${tones[tone]} ${className}`}
      {...props}
    />
  );
}
