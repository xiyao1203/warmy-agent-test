import type { ButtonHTMLAttributes } from "react";

type GhostButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  glowColor?: string;
};

export function GhostButton({
  children,
  className = "",
  glowColor = "var(--primary)",
  ...props
}: GhostButtonProps) {
  return (
    <button
      className={`group relative inline-flex h-9 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-transparent px-4 text-sm font-medium text-[var(--ink)] transition-colors hover:border-[var(--primary)] hover:bg-[var(--primary-subtle)] hover:text-[var(--primary)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      style={
        {
          "--glow-color": glowColor,
        } as React.CSSProperties
      }
      {...props}
    >
      {children}
    </button>
  );
}
