"use client";

import type { HTMLAttributes } from "react";

type TypingIndicatorProps = HTMLAttributes<HTMLDivElement>;

export function TypingIndicator({ className = "", ...props }: TypingIndicatorProps) {
  return (
    <div className={`flex items-center gap-1.5 ${className}`} {...props}>
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="inline-block size-2 animate-bounce rounded-full bg-[var(--accent)]"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
      <span className="text-xs text-[var(--text-muted)]">AI 正在思考...</span>
    </div>
  );
}
