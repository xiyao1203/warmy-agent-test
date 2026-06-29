import type { HTMLAttributes } from "react";

type GlassCardProps = HTMLAttributes<HTMLDivElement>;

export function GlassCard({ children, className = "", ...props }: GlassCardProps) {
  return (
    <div
      className={`rounded-[var(--radius)] border border-white/20 bg-white/10 p-6 shadow-lg backdrop-blur-lg dark:border-white/10 dark:bg-white/5 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
