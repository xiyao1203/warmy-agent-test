import type { HTMLAttributes } from "react";

type ProgressBarProps = HTMLAttributes<HTMLDivElement> & {
  value?: number;
  max?: number;
  showLabel?: boolean;
};

export function ProgressBar({
  className = "",
  max = 100,
  showLabel = false,
  value = 0,
  ...props
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={`w-full ${className}`} {...props}>
      {showLabel && (
        <div className="mb-1 flex justify-between text-sm">
          <span className="text-[var(--text-muted)]">进度</span>
          <span className="font-medium text-[var(--text)]">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--surface-subtle)]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[var(--accent)] to-[var(--accent-strong)] transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
