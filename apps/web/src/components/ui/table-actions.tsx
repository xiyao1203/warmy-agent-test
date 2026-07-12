import type { ButtonHTMLAttributes, ReactNode } from "react";

import { Button } from "./button";
import { Tooltip } from "../uiverse/feedback/tooltip";

export const tableActionHeadClass = "w-28 whitespace-nowrap text-center";

export const tableActionCellClass = "whitespace-nowrap text-center";

export function TableActions({
  children,
  label,
}: {
  children: ReactNode;
  label: string;
}) {
  return (
    <div
      aria-label={`${label} 操作`}
      className="inline-flex items-center justify-center gap-1 whitespace-nowrap"
      role="group"
    >
      {children}
    </div>
  );
}

type TableActionButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  children: ReactNode;
  label: string;
  tone?: "danger" | "default";
};

export function TableActionButton({
  children,
  asChild = false,
  className = "",
  label,
  tone = "default",
  type = "button",
  ...props
}: TableActionButtonProps) {
  return (
    <Tooltip content={label} side="top">
      <Button
        aria-label={label}
        asChild={asChild}
        className={`table-action-button size-8 shrink-0 p-0 ${className}`}
        type={asChild ? undefined : type}
        variant={tone === "danger" ? "danger" : "ghost"}
        {...props}
      >
        {children}
      </Button>
    </Tooltip>
  );
}
