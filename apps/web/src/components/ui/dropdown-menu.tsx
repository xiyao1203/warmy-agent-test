"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import type { ComponentProps } from "react";

export const DropdownMenu = DropdownMenuPrimitive.Root;
export const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;

export function DropdownMenuContent({
  className = "",
  side = "bottom",
  sideOffset = 6,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Content>) {
  return (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Content
        className={`z-50 min-w-40 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface-raised)] p-1 shadow-[var(--shadow-overlay)] ${className}`}
        side={side}
        sideOffset={sideOffset}
        {...props}
      />
    </DropdownMenuPrimitive.Portal>
  );
}

export function DropdownMenuItem({
  className = "",
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Item>) {
  return (
    <DropdownMenuPrimitive.Item
      className={`flex h-8 cursor-default select-none items-center rounded-[var(--radius-sm)] px-2 text-sm text-[var(--ink)] outline-none data-[disabled]:opacity-50 data-[highlighted]:bg-[var(--canvas-soft)] ${className}`}
      {...props}
    />
  );
}

export const DropdownMenuSeparator = DropdownMenuPrimitive.Separator;
