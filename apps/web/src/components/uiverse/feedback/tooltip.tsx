import type { ReactNode } from "react";

type TooltipProps = {
  children: ReactNode;
  content: ReactNode;
  side?: "bottom" | "left" | "right" | "top";
};

const positionClasses = {
  bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
  left: "right-full top-1/2 -translate-y-1/2 mr-2",
  right: "left-full top-1/2 -translate-y-1/2 ml-2",
  top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
};

export function Tooltip({
  children,
  content,
  side = "top",
}: TooltipProps) {
  return (
    <div className="group relative inline-flex">
      {children}
      <div
        className={`pointer-events-none absolute z-50 whitespace-nowrap rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-sm text-[var(--text)] opacity-0 shadow-md transition-opacity group-hover:opacity-100 ${positionClasses[side]}`}
      >
        {content}
      </div>
    </div>
  );
}
