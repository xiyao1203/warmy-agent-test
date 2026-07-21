"use client";

import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { LogOut, User, Settings, Bell, Shield } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

import { logout } from "@/features/auth";
import {
  accountSections,
  normalizeAccountSection,
  type AccountSection,
} from "./types";

const sectionIcons: Record<AccountSection, React.ReactNode> = {
  profile: <User className="size-4" />,
  preferences: <Settings className="size-4" />,
  notifications: <Bell className="size-4" />,
  security: <Shield className="size-4" />,
};

interface AccountCenterProps {
  children: React.ReactNode;
}

export function AccountCenter({ children }: AccountCenterProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeSection = normalizeAccountSection(searchParams.get("section"));
  const [logoutBusy, setLogoutBusy] = useState(false);

  async function handleLogout() {
    setLogoutBusy(true);
    try {
      await logout();
      router.push("/login");
    } finally {
      setLogoutBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1040px] px-4 py-8 sm:px-6 lg:py-10">
      <div className="mb-7 border-b border-[var(--hairline)] pb-6">
        <p className="mb-2 text-sm font-medium text-[var(--muted)]">
          账户与偏好
        </p>
        <h1 className="text-page-title">账户中心</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          管理您的个人信息、偏好设置和安全选项
        </p>
      </div>

      <div className="flex min-w-0 flex-col gap-6 lg:grid lg:grid-cols-[12rem_minmax(0,1fr)] lg:gap-8">
        <nav
          aria-label="账户设置移动导航"
          className="flex gap-1 overflow-x-auto border-b border-[var(--hairline)] pb-2 lg:hidden"
        >
          {accountSections.map((section) => (
            <Link
              aria-current={activeSection === section.id ? "page" : undefined}
              key={section.id}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium transition-colors",
                activeSection === section.id
                  ? "bg-[var(--canvas-soft)] text-[var(--ink)]"
                  : "text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]",
              )}
              href={section.href}
            >
              {sectionIcons[section.id]}
              {section.label}
            </Link>
          ))}
          <div className="mt-2 border-t border-[var(--hairline)] pt-2">
            <button
              className="flex w-full shrink-0 items-center gap-2 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium text-[var(--danger)] transition-colors hover:bg-[var(--danger-subtle)] disabled:opacity-50"
              disabled={logoutBusy}
              onClick={handleLogout}
              type="button"
            >
              <LogOut className="size-4" />
              {logoutBusy ? "退出中..." : "退出登录"}
            </button>
          </div>
        </nav>

        <aside className="hidden lg:block">
          <nav className="sticky top-6 space-y-1" aria-label="账户设置导航">
            {accountSections.map((section) => (
              <Link
                aria-current={activeSection === section.id ? "page" : undefined}
                key={section.id}
                className={cn(
                  "flex items-start gap-3 rounded-[var(--radius-sm)] px-3 py-2.5 text-sm font-medium transition-colors",
                  activeSection === section.id
                    ? "bg-[var(--canvas-soft)] text-[var(--ink)]"
                    : "text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]",
                )}
                href={section.href}
              >
                <span className="mt-0.5">{sectionIcons[section.id]}</span>
                <div className="min-w-0">
                  <div>{section.label}</div>
                  <div className="mt-0.5 text-xs font-normal leading-4 text-[var(--body)]">
                    {section.description}
                  </div>
                </div>
              </Link>
            ))}
            <div className="mt-2 border-t border-[var(--hairline)] pt-2">
              <button
                className="flex w-full items-start gap-3 rounded-[var(--radius-sm)] px-3 py-2.5 text-sm font-medium text-[var(--danger)] transition-colors hover:bg-[var(--danger-subtle)] disabled:opacity-50"
                disabled={logoutBusy}
                onClick={handleLogout}
                type="button"
              >
                <span className="mt-0.5">
                  <LogOut className="size-4" />
                </span>
                <div className="min-w-0 text-left">
                  <div>{logoutBusy ? "退出中..." : "退出登录"}</div>
                  <div className="mt-0.5 text-xs font-normal leading-4 text-[var(--muted)]">
                    安全退出当前账号
                  </div>
                </div>
              </button>
            </div>
          </nav>
        </aside>

        <main className="min-w-0 overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
}
