"use client";

import {
  type CSSProperties,
  type FocusEvent,
  type ReactNode,
  useCallback,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { createPortal } from "react-dom";

type TooltipProps = {
  children: ReactNode;
  className?: string;
  content: ReactNode;
  side?: "bottom" | "left" | "right" | "top";
};

type Position = {
  left: number;
  top: number;
};

const TOOLTIP_GAP = 8;
const VIEWPORT_PADDING = 8;
const subscribeToClient = () => () => undefined;

export function Tooltip({
  children,
  className = "",
  content,
  side = "bottom",
}: TooltipProps) {
  const id = useId();
  const triggerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const suppressHoverRef = useRef(false);
  const mounted = useSyncExternalStore(
    subscribeToClient,
    () => true,
    () => false,
  );
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<Position | null>(null);
  const stringContent = typeof content === "string" ? content : undefined;
  const whitespaceClass =
    stringContent && Array.from(stringContent.trim()).length <= 6
      ? "whitespace-nowrap"
      : "whitespace-normal";

  const updatePosition = useCallback(() => {
    const trigger = triggerRef.current;
    const tooltip = contentRef.current;
    if (!trigger || !tooltip) return;

    setPosition(
      positionTooltip(
        trigger.getBoundingClientRect(),
        tooltip.getBoundingClientRect(),
        side,
      ),
    );
  }, [side]);

  useLayoutEffect(() => {
    if (!mounted || !open) return;
    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [mounted, open, updatePosition]);

  function openTooltip() {
    setPosition(null);
    setOpen(true);
  }

  function closeTooltip() {
    setOpen(false);
  }

  function handleBlur(event: FocusEvent<HTMLDivElement>) {
    if (!event.currentTarget.contains(event.relatedTarget)) closeTooltip();
  }

  function handleMouseLeave() {
    if (triggerRef.current?.matches(":hover")) return;
    suppressHoverRef.current = false;
    if (!triggerRef.current?.querySelector(":focus-visible")) closeTooltip();
  }

  const tooltip = mounted
    ? createPortal(
        <div
          className={`app-tooltip-content pointer-events-none fixed z-[var(--layer-toast)] max-w-[min(18rem,calc(100vw-1rem))] ${whitespaceClass} rounded-[var(--radius-sm)] border border-[var(--hairline)] bg-[var(--surface-raised)] px-2 py-1 text-xs leading-4 text-[var(--ink)] shadow-[var(--shadow-overlay)] transition-[opacity,transform] duration-[var(--motion-fast)] max-sm:hidden`}
          data-state={open ? "open" : "closed"}
          data-tooltip={stringContent}
          id={id}
          ref={contentRef}
          role="tooltip"
          style={tooltipStyle(open, position)}
        >
          {open || !stringContent ? content : null}
        </div>,
        document.body,
      )
    : null;

  return (
    <>
      <div
        className={`app-tooltip-trigger group relative inline-flex min-w-0 max-w-full ${className}`}
        onBlurCapture={handleBlur}
        onContextMenu={closeTooltip}
        onFocusCapture={(event) => {
          if (event.target instanceof HTMLElement) {
            if (event.target.matches(":focus-visible")) openTooltip();
            else closeTooltip();
          }
        }}
        onKeyDownCapture={(event) => {
          if (event.key === "Escape") closeTooltip();
        }}
        onMouseEnter={() => {
          if (!suppressHoverRef.current) openTooltip();
        }}
        onMouseLeave={handleMouseLeave}
        onPointerDown={() => {
          suppressHoverRef.current = true;
          closeTooltip();
        }}
        ref={triggerRef}
      >
        {children}
      </div>
      {tooltip}
    </>
  );
}

function tooltipStyle(open: boolean, position: Position | null): CSSProperties {
  return {
    left: position?.left ?? -9999,
    opacity: open && position ? 1 : 0,
    top: position?.top ?? -9999,
    transform: open && position ? "scale(1)" : "scale(0.98)",
  };
}

function positionTooltip(
  trigger: DOMRect,
  tooltip: DOMRect,
  side: NonNullable<TooltipProps["side"]>,
): Position {
  const viewportWidth =
    document.documentElement.clientWidth || window.innerWidth;
  const viewportHeight =
    document.documentElement.clientHeight || window.innerHeight;
  let left = trigger.left + (trigger.width - tooltip.width) / 2;
  let top = trigger.top + (trigger.height - tooltip.height) / 2;

  if (side === "right") left = trigger.right + TOOLTIP_GAP;
  if (side === "left") left = trigger.left - tooltip.width - TOOLTIP_GAP;
  if (side === "bottom") top = trigger.bottom + TOOLTIP_GAP;
  if (side === "top") top = trigger.top - tooltip.height - TOOLTIP_GAP;

  if (
    side === "right" &&
    left + tooltip.width > viewportWidth - VIEWPORT_PADDING
  ) {
    left = trigger.left - tooltip.width - TOOLTIP_GAP;
  }
  if (side === "left" && left < VIEWPORT_PADDING) {
    left = trigger.right + TOOLTIP_GAP;
  }
  if (
    side === "bottom" &&
    top + tooltip.height > viewportHeight - VIEWPORT_PADDING
  ) {
    top = trigger.top - tooltip.height - TOOLTIP_GAP;
  }
  if (side === "top" && top < VIEWPORT_PADDING) {
    top = trigger.bottom + TOOLTIP_GAP;
  }

  return {
    left: clamp(
      left,
      VIEWPORT_PADDING,
      viewportWidth - tooltip.width - VIEWPORT_PADDING,
    ),
    top: clamp(
      top,
      VIEWPORT_PADDING,
      viewportHeight - tooltip.height - VIEWPORT_PADDING,
    ),
  };
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), Math.max(minimum, maximum));
}
