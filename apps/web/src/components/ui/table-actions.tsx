import type { ReactNode } from "react";

export const tableActionHeadClass =
  "w-32 min-w-32 whitespace-nowrap text-center";

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
      className="inline-flex items-center justify-center gap-1.5 whitespace-nowrap"
      role="group"
    >
      {children}
    </div>
  );
}
