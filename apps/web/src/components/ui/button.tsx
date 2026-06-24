import { Slot } from "@radix-ui/react-slot";
import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
};

export function Button({
  asChild = false,
  className = "",
  ...props
}: ButtonProps) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      className={`inline-flex h-8 items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 text-sm font-medium transition-colors hover:bg-[var(--surface-subtle)] disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      {...props}
    />
  );
}
