import {
  Bot,
  Boxes,
  ClipboardCheck,
  FlaskConical,
  LayoutDashboard,
  Play,
} from "lucide-react";
import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
  projectName: string;
  userName: string;
};

const navigation = [
  { label: "概览", icon: LayoutDashboard },
  { label: "测试 Agent", icon: Bot },
  { label: "Agent 与版本", icon: Boxes },
  { label: "测试集", icon: FlaskConical },
  { label: "测试计划", icon: ClipboardCheck },
  { label: "运行记录", icon: Play },
];

export function AppShell({ children, projectName, userName }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--text)]">
      <header className="flex h-12 items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-4">
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold">Warmy Agent Test</span>
          <button
            className="rounded-md px-2 py-1 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-subtle)]"
            type="button"
          >
            {projectName}
          </button>
        </div>
        <button
          className="flex size-7 items-center justify-center rounded-full bg-[var(--surface-subtle)] text-xs font-semibold"
          title={userName}
          type="button"
        >
          {userName.slice(0, 1).toUpperCase()}
          <span className="sr-only">{userName}</span>
        </button>
      </header>
      <div className="grid min-h-[calc(100vh-3rem)] grid-cols-[14rem_1fr] max-[1279px]:grid-cols-[4rem_1fr]">
        <aside className="border-r border-[var(--border)] bg-[var(--surface)] p-2">
          <nav aria-label="主导航" className="space-y-1">
            {navigation.map(({ icon: Icon, label }) => (
              <a
                className="flex h-9 items-center gap-3 rounded-md px-3 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text)] max-[1279px]:justify-center max-[1279px]:px-0"
                href="#"
                key={label}
                title={label}
              >
                <Icon aria-hidden="true" className="size-4 shrink-0" />
                <span className="max-[1279px]:sr-only">{label}</span>
              </a>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 p-6">{children}</main>
      </div>
    </div>
  );
}
