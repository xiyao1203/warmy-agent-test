"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ComponentProps } from "react";

export const Drawer = DialogPrimitive.Root;
export const DrawerTrigger = DialogPrimitive.Trigger;
export const DrawerClose = DialogPrimitive.Close;
export const DrawerTitle = ({
  className = "",
  ...props
}: ComponentProps<typeof DialogPrimitive.Title>) => (
  <DialogPrimitive.Title
    className={`text-lg font-semibold text-[var(--ink)] ${className}`}
    {...props}
  />
);
export const DrawerDescription = ({
  className = "",
  ...props
}: ComponentProps<typeof DialogPrimitive.Description>) => (
  <DialogPrimitive.Description
    className={`mt-1 text-sm leading-5 text-[var(--muted)] ${className}`}
    {...props}
  />
);

export function DrawerContent({
  children,
  className = "",
  ...props
}: ComponentProps<typeof DialogPrimitive.Content>) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="precision-overlay fixed inset-0 z-40 bg-[var(--overlay)]" />
      <DialogPrimitive.Content
        className={`precision-drawer-content fixed inset-y-0 right-0 z-50 w-[min(30rem,calc(100vw-2rem))] border-l border-[var(--hairline)] bg-[var(--surface-raised)] p-5 shadow-[var(--shadow-overlay)] focus:outline-none ${className}`}
        {...props}
      >
        {children}
        <DialogPrimitive.Close
          aria-label="关闭详情"
          className="absolute right-3 top-3 flex size-8 items-center justify-center rounded-[var(--radius-md)] text-[var(--muted)] hover:bg-[var(--canvas-soft)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        >
          <X aria-hidden="true" className="size-4" />
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
