"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  User,
  Settings,
  Bell,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";

import { accountSections, type AccountSection } from "./types";

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
  const activeSection = (searchParams.get("section") || "profile") as AccountSection;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">账户中心</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          管理您的个人信息、偏好设置和安全选项
        </p>
      </div>

      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[13rem_minmax(0,1fr)]">
        {/* Mobile: scrollable horizontal nav */}
        <nav
          className="flex gap-2 overflow-x-auto pb-2 lg:hidden"
          aria-label="账户设置导航"
        >
          {accountSections.map((section) => (
            <Link
              key={section.id}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                activeSection === section.id
                  ? "bg-[var(--primary)] text-[var(--primary-fg)]"
                  : "text-[var(--text-muted)] hover:bg-[var(--accent)] hover:text-[var(--text)]"
              )}
              href={section.href}
            >
              {sectionIcons[section.id]}
              {section.label}
            </Link>
          ))}
        </nav>

        {/* Desktop: vertical sidebar */}
        <aside className="hidden lg:block">
          <nav className="sticky top-6 space-y-1" aria-label="账户设置导航">
            {accountSections.map((section) => (
              <Link
                key={section.id}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  activeSection === section.id
                    ? "bg-[var(--primary)] text-[var(--primary-fg)]"
                    : "text-[var(--text-muted)] hover:bg-[var(--accent)] hover:text-[var(--text)]"
                )}
                href={section.href}
              >
                {sectionIcons[section.id]}
                <div>
                  <div>{section.label}</div>
                  <div className="text-xs font-normal opacity-70">
                    {section.description}
                  </div>
                </div>
              </Link>
            ))}
          </nav>
        </aside>

        {/* Main content */}
        <main className="min-w-0 overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
}
