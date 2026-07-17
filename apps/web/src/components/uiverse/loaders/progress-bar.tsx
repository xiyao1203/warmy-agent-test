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
          <span className="text-[var(--muted)]">进度</span>
          <span className="font-medium text-[var(--ink)]">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--canvas-soft)]">
        <div
          className="h-full rounded-full bg-[var(--primary)] transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
