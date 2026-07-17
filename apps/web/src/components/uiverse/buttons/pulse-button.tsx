"use client";

import { LoaderCircle } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";

type PulseButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
  pulse?: boolean;
};

export function PulseButton({
  children,
  className = "",
  loading = false,
  pulse = true,
  ...props
}: PulseButtonProps) {
  return (
    <button
      className={`group relative inline-flex h-9 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--primary)] bg-[var(--primary)] px-4 text-sm font-medium text-[var(--on-primary)] transition-colors hover:bg-[var(--primary-active)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${pulse ? "animate-pulse-subtle" : ""} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
      ) : null}
      {children}
      <span className="absolute inset-0 rounded-[var(--radius-md)] bg-white/20 opacity-0 transition-opacity group-hover:opacity-100" />
    </button>
  );
}
