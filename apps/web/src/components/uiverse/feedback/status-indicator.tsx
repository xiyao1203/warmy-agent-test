import type { HTMLAttributes } from "react";

type StatusType =
  | "error"
  | "info"
  | "offline"
  | "running"
  | "success"
  | "warning";

type StatusIndicatorProps = HTMLAttributes<HTMLDivElement> & {
  status: StatusType;
  label?: string;
  size?: "lg" | "md" | "sm";
};

const statusConfig = {
  error: {
    bg: "bg-[var(--danger)]",
    pulse: "animate-pulse",
    text: "text-[var(--danger)]",
  },
  info: {
    bg: "bg-[var(--info)]",
    pulse: "",
    text: "text-[var(--info)]",
  },
  offline: {
    bg: "bg-[var(--muted)]",
    pulse: "",
    text: "text-[var(--muted)]",
  },
  running: {
    bg: "bg-[var(--success)]",
    pulse: "animate-pulse",
    text: "text-[var(--success)]",
  },
  success: {
    bg: "bg-[var(--success)]",
    pulse: "",
    text: "text-[var(--success)]",
  },
  warning: {
    bg: "bg-[var(--warning)]",
    pulse: "animate-pulse",
    text: "text-[var(--warning)]",
  },
};

const sizeClasses = {
  lg: "size-3",
  md: "size-2",
  sm: "size-1.5",
};

export function StatusIndicator({
  className = "",
  label,
  size = "md",
  status,
  ...props
}: StatusIndicatorProps) {
  const config = statusConfig[status];

  return (
    <div className={`inline-flex items-center gap-2 ${className}`} {...props}>
      <span className="relative flex">
        <span
          className={`inline-flex rounded-full ${config.bg} ${sizeClasses[size]} ${config.pulse}`}
        />
        {config.pulse && (
          <span
            className={`absolute inline-flex h-full w-full rounded-full ${config.bg} opacity-75 ${config.pulse}`}
          />
        )}
      </span>
      {label && (
        <span className={`text-sm font-medium ${config.text}`}>{label}</span>
      )}
    </div>
  );
}
