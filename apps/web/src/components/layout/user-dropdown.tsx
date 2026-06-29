"use client";

import { LogOut, Settings, User } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

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
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        aria-expanded={open}
        aria-haspopup="true"
        aria-label="用户菜单"
        className="flex h-8 shrink-0 items-center gap-2 rounded-[var(--radius-sm)] px-2 text-sm transition-colors hover:bg-[var(--surface-subtle)]"
        onClick={() => setOpen(!open)}
        title={`${displayName} · ${email}`}
        type="button"
      >
        <span className="grid size-7 place-items-center rounded-full bg-[var(--accent)] text-xs font-semibold text-white">
          {displayName.slice(0, 1).toUpperCase()}
        </span>
        <span className="max-[900px]:hidden">{displayName}</span>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full z-50 mt-1 min-w-[14rem] rounded-lg border border-[var(--border)] bg-[var(--surface)] py-1 shadow-lg"
          role="menu"
        >
          <div className="border-b border-[var(--border)] px-4 py-3">
            <p className="text-sm font-semibold">{displayName}</p>
            <p className="mt-0.5 text-xs text-[var(--text-muted)]">{email}</p>
          </div>
          <Link
            className="flex items-center gap-3 px-4 py-2.5 text-sm transition-colors hover:bg-[var(--surface-subtle)]"
            href="/account?section=profile"
            onClick={() => setOpen(false)}
            role="menuitem"
          >
            <User className="size-4 text-[var(--text-muted)]" />
            <div>
              <p className="font-medium">个人资料</p>
              <p className="text-xs text-[var(--text-muted)]">
                管理您的个人信息
              </p>
            </div>
          </Link>
          <Link
            className="flex items-center gap-3 px-4 py-2.5 text-sm transition-colors hover:bg-[var(--surface-subtle)]"
            href="/account?section=preferences"
            onClick={() => setOpen(false)}
            role="menuitem"
          >
            <Settings className="size-4 text-[var(--text-muted)]" />
            <div>
              <p className="font-medium">设置</p>
              <p className="text-xs text-[var(--text-muted)]">
                偏好设置与账号安全
              </p>
            </div>
          </Link>
          <div className="border-t border-[var(--border)]" />
          <button
            className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-[var(--error)] transition-colors hover:bg-[var(--error-subtle)]"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
            role="menuitem"
            type="button"
          >
            <LogOut className="size-4" />
            <div>
              <p className="font-medium">退出登录</p>
              <p className="text-xs text-[var(--text-muted)]">
                安全退出当前账号
              </p>
            </div>
          </button>
        </div>
      )}
    </div>
  );
}
