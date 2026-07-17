import { LoaderCircle } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";

type GradientButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
};

export function GradientButton({
  children,
  className = "",
  loading = false,
  ...props
}: GradientButtonProps) {
  return (
    <button
      className={`inline-flex h-9 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--primary)] bg-[var(--primary)] px-4 text-sm font-medium text-[var(--on-primary)] transition-colors hover:bg-[var(--primary-active)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
      ) : null}
      {children}
    </button>
  );
}
