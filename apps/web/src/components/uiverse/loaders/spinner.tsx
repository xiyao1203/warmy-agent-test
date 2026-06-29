import type { HTMLAttributes } from "react";

type SpinnerProps = HTMLAttributes<HTMLDivElement> & {
  size?: "lg" | "md" | "sm";
};

const sizeClasses = {
  lg: "size-8",
  md: "size-5",
  sm: "size-4",
};

export function Spinner({ className = "", size = "md", ...props }: SpinnerProps) {
  return (
    <div
      aria-label="加载中"
      className={`animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--accent)] ${sizeClasses[size]} ${className}`}
      role="status"
      {...props}
    >
      <span className="sr-only">加载中...</span>
    </div>
  );
}
