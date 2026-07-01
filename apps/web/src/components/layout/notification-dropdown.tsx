"use client";

import { Bell, Settings } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

export function NotificationDropdown() {
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
        aria-label="通知"
        className="flex h-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] px-2 text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
        onClick={() => setOpen(!open)}
        type="button"
      >
        <Bell className="size-4" />
      </button>

      {open && (
        <div
          className="absolute right-0 top-full z-50 mt-1 min-w-[20rem] rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]"
          role="menu"
        >
          <div className="border-b border-[var(--hairline)] px-4 py-3">
            <h3 className="font-semibold">通知中心</h3>
          </div>
          <div className="p-8 text-center">
            <Bell className="mx-auto size-8 text-[var(--muted)]" />
            <p className="mt-3 text-sm text-[var(--muted)]">暂无新通知</p>
            <Link
              className="mt-3 inline-flex items-center gap-2 text-sm text-[var(--primary)] hover:underline"
              href="/account?section=notifications"
              onClick={() => setOpen(false)}
            >
              <Settings className="size-3.5" />
              通知偏好设置
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
