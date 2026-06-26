import { Slot } from "@radix-ui/react-slot";
import { LoaderCircle } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  loading?: boolean;
  variant?: "danger" | "ghost" | "primary" | "secondary";
};

export function Button({
  asChild = false,
  children,
  className = "",
  loading = false,
  variant = "secondary",
  ...props
}: ButtonProps) {
  const Component = asChild ? Slot : "button";
  const variants = {
    danger:
      "border-[var(--danger)] bg-[var(--surface)] text-[var(--danger)] hover:bg-[var(--danger-subtle)]",
    ghost:
      "border-transparent bg-transparent text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]",
    primary:
      "border-[var(--accent)] bg-[var(--accent)] text-white hover:bg-[var(--accent-strong)]",
    secondary:
      "border-[var(--border)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--surface-subtle)]",
  };

  return (
    <Component
      className={`inline-flex h-8 items-center justify-center gap-2 rounded-[var(--radius-sm)] border px-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
      disabled={loading || props.disabled}
    >
      {asChild ? (
        children
      ) : (
        <>
          {loading ? (
            <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
          ) : null}
          {children}
        </>
      )}
    </Component>
  );
}
