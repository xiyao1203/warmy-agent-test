"use client";

import { Bot } from "lucide-react";
import { useEffect, useState } from "react";

type ChatEmptyStateProps = {
  title?: string;
  description?: string;
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;
};

export function ChatEmptyState({
  description = "例如：\"测试登录流程，使用 admin 账号\"",
  onSuggestionClick,
  suggestions = [],
  title = "告诉我您想测试什么",
}: ChatEmptyStateProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div
      className={`flex h-full flex-col items-center justify-center transition-all duration-700 ${
        mounted ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
      }`}
    >
      <div className="relative">
        <Bot className="size-16 text-[var(--text-muted)]" />
        <div className="absolute -right-1 -top-1 size-4 animate-pulse rounded-full bg-[var(--accent)]" />
      </div>
      <p className="mt-6 text-lg font-semibold text-[var(--text)]">{title}</p>
      <p className="mt-2 text-sm text-[var(--text-muted)]">{description}</p>
      {suggestions.length > 0 && (
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {suggestions.map((suggestion, i) => (
            <button
              key={i}
              className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-xs text-[var(--text-muted)] transition-all hover:border-[var(--accent)] hover:text-[var(--accent)] hover:shadow-sm"
              onClick={() => onSuggestionClick?.(suggestion)}
              style={{
                animationDelay: `${i * 100}ms`,
                opacity: mounted ? 1 : 0,
                transform: mounted ? "translateY(0)" : "translateY(10px)",
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
