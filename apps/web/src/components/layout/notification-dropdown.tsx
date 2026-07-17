"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { Bell, Settings } from "lucide-react";
import Link from "next/link";

export function NotificationDropdown() {
  return (
    <DropdownMenuPrimitive.Root>
      <DropdownMenuPrimitive.Trigger asChild>
        <button aria-label="通知" className="app-icon-button" type="button">
          <Bell aria-hidden="true" className="size-4" />
        </button>
      </DropdownMenuPrimitive.Trigger>
      <DropdownMenuPrimitive.Portal>
        <DropdownMenuPrimitive.Content
          align="end"
          aria-label="通知中心"
          className="app-menu w-72"
          sideOffset={7}
        >
          <DropdownMenuPrimitive.Label className="border-b border-[var(--hairline)] px-3 py-2.5 text-sm font-semibold">
            通知中心
          </DropdownMenuPrimitive.Label>
          <div className="px-4 py-7 text-center">
            <Bell
              aria-hidden="true"
              className="mx-auto size-7 text-[var(--muted)]"
            />
            <p className="mt-3 text-sm text-[var(--muted)]">暂无新通知</p>
          </div>
          <DropdownMenuPrimitive.Separator className="h-px bg-[var(--hairline)]" />
          <DropdownMenuPrimitive.Item asChild>
            <Link
              className="app-menu-item justify-center text-[var(--primary)]"
              href="/account?section=notifications"
            >
              <Settings aria-hidden="true" className="size-3.5" />
              通知偏好设置
            </Link>
          </DropdownMenuPrimitive.Item>
        </DropdownMenuPrimitive.Content>
      </DropdownMenuPrimitive.Portal>
    </DropdownMenuPrimitive.Root>
  );
}
