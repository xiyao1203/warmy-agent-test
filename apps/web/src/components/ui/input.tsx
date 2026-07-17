import { forwardRef, type InputHTMLAttributes } from "react";

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(function Input({ className = "", ...props }, ref) {
  return (
    <input
      className={`h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 text-sm text-[var(--ink)] placeholder:text-[var(--muted-soft)] hover:border-[var(--hairline-strong)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring-subtle)] disabled:cursor-not-allowed disabled:bg-[var(--canvas-soft)] disabled:text-[var(--muted-soft)] ${className}`}
      ref={ref}
      {...props}
    />
  );
});
