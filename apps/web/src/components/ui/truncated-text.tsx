import type { ReactNode } from "react";

import { Tooltip } from "@/components/uiverse/feedback/tooltip";

type TruncatedTextProps = {
  children: ReactNode;
  className?: string;
  value?: string;
};

export function TruncatedText({
  children,
  className = "",
  value,
}: TruncatedTextProps) {
  const fullValue = value ?? (typeof children === "string" ? children : "");

  return (
    <Tooltip content={fullValue} side="top">
      <span
        aria-label={fullValue || undefined}
        className={`block min-w-0 max-w-full truncate outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] ${className}`}
        tabIndex={fullValue ? 0 : undefined}
      >
        {children}
      </span>
    </Tooltip>
  );
}
