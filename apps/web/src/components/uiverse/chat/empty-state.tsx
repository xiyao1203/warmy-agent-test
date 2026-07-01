"use client";

import { Bot } from "lucide-react";

type ChatEmptyStateProps = {
  title?: string;
  description?: string;
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;
};

export function ChatEmptyState({
  description = '例如："测试登录流程，使用 admin 账号"',
  onSuggestionClick,
  suggestions = [],
  title = "告诉我您想测试什么",
}: ChatEmptyStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4">
      <div className="mb-6 flex size-16 items-center justify-center rounded-full bg-[var(--primary-subtle)]">
        <Bot className="size-8 text-[var(--primary)]" />
      </div>
      <h1 className="text-2xl font-semibold text-[var(--ink)]">{title}</h1>
      <p className="mt-2 text-[0.9375rem] text-[var(--muted)]">{description}</p>
      {suggestions.length > 0 && (
        <div className="mt-8 flex flex-wrap justify-center gap-2 max-w-xl">
          {suggestions.map((suggestion, i) => (
            <button
              key={i}
              className="rounded-xl border border-[var(--hairline)] bg-[var(--surface)] px-4 py-2.5 text-[0.875rem] text-[var(--ink)] transition-all hover:border-[var(--hairline-strong)] hover:bg-[var(--canvas-soft)] hover:shadow-sm"
              onClick={() => onSuggestionClick?.(suggestion)}
              style={{
                animationDelay: `${i * 80}ms`,
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
