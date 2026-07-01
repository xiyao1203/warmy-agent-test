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
    <div className="flex h-full flex-col items-center justify-center opacity-100 transition-all duration-700">
      <div className="relative">
        <Bot className="size-16 text-[var(--muted)]" />
        <div className="absolute -right-1 -top-1 size-4 animate-pulse rounded-full bg-[var(--primary)]" />
      </div>
      <p className="mt-6 text-lg font-semibold text-[var(--ink)]">{title}</p>
      <p className="mt-2 text-sm text-[var(--muted)]">{description}</p>
      {suggestions.length > 0 && (
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {suggestions.map((suggestion, i) => (
            <button
              key={i}
              className="rounded-full border border-[var(--hairline)] bg-[var(--surface)] px-3 py-1.5 text-xs text-[var(--muted)] transition-all hover:border-[var(--primary)] hover:text-[var(--primary)] hover:shadow-sm"
              onClick={() => onSuggestionClick?.(suggestion)}
              style={{
                animationDelay: `${i * 100}ms`,
                opacity: 1,
                transform: "translateY(0)",
                transition: `all 0.5s ease ${i * 100}ms`,
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
