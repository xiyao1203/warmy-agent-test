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
    bg: "bg-red-500",
    pulse: "animate-pulse",
    text: "text-red-600 dark:text-red-400",
  },
  info: {
    bg: "bg-blue-500",
    pulse: "",
    text: "text-blue-600 dark:text-blue-400",
  },
  offline: {
    bg: "bg-gray-400",
    pulse: "",
    text: "text-gray-600 dark:text-gray-400",
  },
  running: {
    bg: "bg-emerald-500",
    pulse: "animate-pulse",
    text: "text-emerald-600 dark:text-emerald-400",
  },
  success: {
    bg: "bg-emerald-500",
    pulse: "",
    text: "text-emerald-600 dark:text-emerald-400",
  },
  warning: {
    bg: "bg-amber-500",
    pulse: "animate-pulse",
    text: "text-amber-600 dark:text-amber-400",
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
