"use client";

import { ArrowLeft, MessageSquare } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import { helpNavigation, isHelpDestinationActive } from "./help-navigation";

interface HelpShellProps {
  children: ReactNode;
}

function NavigationLinks({ pathname }: { pathname: string }) {
  return helpNavigation.map(({ href, icon: Icon, label }) => {
    const isActive = isHelpDestinationActive(pathname, href);

    return (
      <Link
        aria-current={isActive ? "page" : undefined}
        className={cn(
          "flex shrink-0 items-center gap-2 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium transition-colors",
          isActive
            ? "bg-[var(--surface-subtle)] text-[var(--text)]"
            : "text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]"
        )}
        href={href}
        key={href}
      >
        <Icon className="size-4" />
        {label}
      </Link>
    );
  });
}

export function HelpShell({ children }: HelpShellProps) {
  const pathname = usePathname() || "/docs";

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--surface)]/95 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-[1180px] items-center justify-between gap-4 px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-4">
            <Link
              className="flex shrink-0 items-center gap-2 text-sm font-medium text-[var(--text-muted)] transition-colors hover:text-[var(--text)]"
              href="/projects"
            >
              <ArrowLeft className="size-4" />
              返回应用
            </Link>
            <span className="hidden h-4 w-px bg-[var(--border)] sm:block" />
            <span className="truncate text-sm font-semibold">帮助中心</span>
          </div>
          <Link
            className="flex shrink-0 items-center gap-2 rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-1.5 text-sm font-medium transition-colors hover:bg-[var(--surface-subtle)]"
            href="/feedback"
          >
            <MessageSquare className="size-4" />
            提交反馈
          </Link>
        </div>
      </header>

      <nav
        aria-label="帮助中心移动目录"
        className="overflow-x-auto border-b border-[var(--border)] bg-[var(--surface)] px-4 py-2 lg:hidden"
      >
        <div className="flex min-w-max gap-1">
          <NavigationLinks pathname={pathname} />
        </div>
      </nav>

      <div className="mx-auto grid max-w-[1180px] grid-cols-1 lg:grid-cols-[12rem_minmax(0,1fr)]">
        <aside className="hidden border-r border-[var(--border)] px-4 py-8 lg:block">
          <nav
            aria-label="帮助中心目录"
            className="sticky top-22 space-y-1"
          >
            <NavigationLinks pathname={pathname} />
          </nav>
        </aside>
        <main className="min-w-0 px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
          {children}
        </main>
      </div>
    </div>
  );
}
