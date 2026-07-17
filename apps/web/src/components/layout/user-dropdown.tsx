"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { LogOut, Settings, User } from "lucide-react";
import Link from "next/link";

type UserDropdownProps = {
  displayName: string;
  email: string;
  onLogout: () => void;
};

export function UserDropdown({
  displayName,
  email,
  onLogout,
}: UserDropdownProps) {
  return (
    <DropdownMenuPrimitive.Root>
      <DropdownMenuPrimitive.Trigger asChild>
        <button
          aria-label="用户菜单"
          className="flex h-8 shrink-0 items-center gap-2 rounded-[var(--radius-md)] px-2 text-sm transition-colors hover:bg-[var(--canvas-soft)]"
          title={`${displayName} · ${email}`}
          type="button"
        >
          <span className="grid size-7 place-items-center rounded-full bg-[var(--primary)] text-xs font-semibold text-[var(--on-primary)]">
            {displayName.slice(0, 1).toUpperCase()}
          </span>
          <span className="max-[900px]:hidden">{displayName}</span>
        </button>
      </DropdownMenuPrimitive.Trigger>
      <DropdownMenuPrimitive.Portal>
        <DropdownMenuPrimitive.Content
          align="end"
          aria-label="用户菜单"
          className="app-menu w-56"
          sideOffset={7}
        >
          <DropdownMenuPrimitive.Label className="border-b border-[var(--hairline)] px-3 py-2.5">
            <span className="block text-sm font-semibold">{displayName}</span>
            <span className="mt-0.5 block truncate text-xs font-normal text-[var(--muted)]">
              {email}
            </span>
          </DropdownMenuPrimitive.Label>
          <div className="py-1">
            <DropdownMenuPrimitive.Item asChild>
              <Link
                className="app-menu-item min-h-10 px-3"
                href="/account?section=profile"
              >
                <User
                  aria-hidden="true"
                  className="size-4 text-[var(--muted)]"
                />
                个人资料
              </Link>
            </DropdownMenuPrimitive.Item>
            <DropdownMenuPrimitive.Item asChild>
              <Link
                className="app-menu-item min-h-10 px-3"
                href="/account?section=preferences"
              >
                <Settings
                  aria-hidden="true"
                  className="size-4 text-[var(--muted)]"
                />
                偏好设置与账号安全
              </Link>
            </DropdownMenuPrimitive.Item>
          </div>
          <DropdownMenuPrimitive.Separator className="h-px bg-[var(--hairline)]" />
          <DropdownMenuPrimitive.Item asChild>
            <button
              className="app-menu-item w-full px-3 text-[var(--danger)] data-[highlighted]:bg-[var(--danger-subtle)]"
              onClick={onLogout}
              type="button"
            >
              <LogOut aria-hidden="true" className="size-4" />
              退出登录
            </button>
          </DropdownMenuPrimitive.Item>
        </DropdownMenuPrimitive.Content>
      </DropdownMenuPrimitive.Portal>
    </DropdownMenuPrimitive.Root>
  );
}
