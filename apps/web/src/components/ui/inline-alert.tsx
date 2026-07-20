import { AlertTriangle, CheckCircle2, CircleAlert, Info } from "lucide-react";
import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type InlineAlertTone = "danger" | "info" | "success" | "warning";

const toneIcons = {
  danger: CircleAlert,
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
};

type InlineAlertProps = HTMLAttributes<HTMLDivElement> & {
  action?: ReactNode;
  icon?: ReactNode;
  title: string;
  tone?: InlineAlertTone;
};

export function InlineAlert({
  action,
  children,
  className,
  icon,
  title,
  tone = "info",
  ...props
}: InlineAlertProps) {
  const Icon = toneIcons[tone];
  const urgent = tone === "danger" || tone === "warning";

  return (
    <div
      className={cn("precision-inline-alert", className)}
      data-tone={tone}
      role={urgent ? "alert" : "status"}
      {...props}
    >
      <span className="precision-inline-alert-icon">
        {icon ?? <Icon aria-hidden="true" />}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-[var(--ink)]">{title}</p>
        <div className="mt-1 text-sm leading-5 text-[var(--muted)]">
          {children}
        </div>
      </div>
      {action ? (
        <div className="precision-inline-alert-action">{action}</div>
      ) : null}
    </div>
  );
}
