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
      className={`group relative inline-flex h-9 items-center justify-center gap-2 rounded-[var(--radius-sm)] border border-[var(--accent)] bg-[var(--accent)] px-4 text-sm font-medium text-white transition-all hover:bg-[var(--accent-strong)] hover:shadow-[0_0_20px_rgba(var(--accent-rgb,59,130,246),0.5)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50 ${pulse ? "animate-pulse-subtle" : ""} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
      ) : null}
      {children}
      <span className="absolute inset-0 rounded-[var(--radius-sm)] bg-white/20 opacity-0 transition-opacity group-hover:opacity-100" />
    </button>
  );
}
