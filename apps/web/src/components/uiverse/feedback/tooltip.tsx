import type { ReactNode } from "react";

type TooltipProps = {
  children: ReactNode;
  className?: string;
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
  className = "",
  content,
  side = "bottom",
}: TooltipProps) {
  const stringContent = typeof content === "string" ? content : undefined;
  const whitespaceClass =
    stringContent && Array.from(stringContent.trim()).length <= 6
      ? "whitespace-nowrap"
      : "whitespace-normal";

  return (
    <div
      className={`group relative inline-flex min-w-0 max-w-full ${className}`}
    >
      {children}
      <div
        className={`pointer-events-none absolute z-50 max-w-[min(18rem,calc(100vw-1rem))] ${whitespaceClass} rounded-[var(--radius-sm)] border border-[var(--hairline)] bg-[var(--surface-raised)] px-2 py-1 text-xs leading-4 text-[var(--ink)] opacity-0 shadow-[var(--shadow-overlay)] transition-[opacity,transform] duration-[var(--motion-fast)] after:content-[attr(data-tooltip)] group-hover:opacity-100 group-focus-within:opacity-100 max-sm:hidden ${positionClasses[side]}`}
        data-tooltip={stringContent}
        role="tooltip"
      >
        {stringContent ? null : content}
      </div>
    </div>
  );
}
