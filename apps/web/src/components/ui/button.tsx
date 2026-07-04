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
  const variants: Record<string, string> = {
    danger:
      "border-[var(--danger)] bg-[var(--surface)] text-[var(--danger)] hover:bg-[var(--danger-subtle)]",
    ghost:
      "border-transparent bg-transparent text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]",
    primary:
      "border-transparent bg-[var(--primary)] text-white hover:bg-[var(--primary-active)] active:scale-[0.97]",
    secondary:
      "border-[var(--hairline-strong)] bg-[var(--surface)] text-[var(--ink)] hover:bg-[var(--canvas-soft)]",
  };

  const shape =
    variant === "primary"
      ? "rounded-[var(--radius-pill)] px-5"
      : "rounded-[var(--radius-sm)] px-4";

  return (
    <Component
      className={`inline-flex h-9 items-center justify-center gap-1.5 border text-sm font-medium transition-all disabled:cursor-not-allowed disabled:opacity-50 ${shape} ${variants[variant]} ${className}`}
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
