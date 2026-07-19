import { forwardRef, type SelectHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, ...props }, ref) {
    return (
      <select
        className={cn(
          "h-9 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 text-sm text-[var(--ink)] hover:border-[var(--hairline-strong)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring-subtle)] disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
