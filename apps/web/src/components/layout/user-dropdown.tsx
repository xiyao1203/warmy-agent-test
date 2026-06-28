"use client";

import { LogOut, Settings, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type UserDropdownProps = {
  displayName: string;
  email: string;
  onLogout: () => void;
};

export function UserDropdown({ displayName, email, onLogout }: UserDropdownProps) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
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
          className="absolute right-0 top-full z-50 mt-1 min-w-[12rem] rounded-lg border border-[var(--border)] bg-[var(--surface)] py-1 shadow-lg"
          role="menu"
        >
          <div className="border-b border-[var(--border)] px-3 py-2">
            <p className="text-sm font-medium">{displayName}</p>
            <p className="text-xs text-[var(--text-muted)]">{email}</p>
          </div>
          <button
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]"
            onClick={() => setOpen(false)}
            role="menuitem"
            type="button"
          >
            <User className="size-4" />
            个人资料
          </button>
          <button
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]"
            onClick={() => setOpen(false)}
            role="menuitem"
            type="button"
          >
            <Settings className="size-4" />
            设置
          </button>
          <div className="border-t border-[var(--border)]" />
          <button
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--error)] transition-colors hover:bg-[var(--error-subtle)]"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
            role="menuitem"
            type="button"
          >
            <LogOut className="size-4" />
            退出登录
          </button>
        </div>
      )}
    </div>
  );
}
