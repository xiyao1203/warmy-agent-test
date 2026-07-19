import type { ButtonHTMLAttributes, HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Pagination({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return (
    <nav
      aria-label="分页"
      className={cn("flex items-center gap-1", className)}
      {...props}
    />
  );
}

export function PaginationButton({
  active = false,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { active?: boolean }) {
  return (
    <button
      aria-current={active ? "page" : undefined}
      className={cn(
        "inline-flex size-8 items-center justify-center rounded-[var(--radius-md)] border text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40",
        active
          ? "border-[var(--primary)] bg-[var(--primary-subtle)] text-[var(--primary)]"
          : "border-transparent text-[var(--muted)] hover:border-[var(--hairline)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]",
        className,
      )}
      type="button"
      {...props}
    />
  );
}
