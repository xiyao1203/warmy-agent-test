"use client";

import { Bot, User } from "lucide-react";
import { useEffect, useState } from "react";

import { MarkdownContent } from "./markdown-content";

type MessageBubbleProps = {
  content: string;
  role: "assistant" | "user";
  animate?: boolean;
  isStreaming?: boolean;
  timestamp?: string;
};

export function MessageBubble({
  animate = true,
  content,
  isStreaming = false,
  role,
  timestamp,
}: MessageBubbleProps) {
  const [visible, setVisible] = useState(!animate);
  const isUser = role === "user";

  useEffect(() => {
    if (animate) {
      const timer = setTimeout(() => setVisible(true), 50);
      return () => clearTimeout(timer);
    }
  }, [animate]);

  return (
    <div
      className={`flex gap-3 transition-all duration-300 ${
        isUser ? "flex-row-reverse" : ""
      } ${visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"}`}
    >
      <div
        className={`flex size-8 shrink-0 items-center justify-center rounded-full transition-transform duration-300 hover:scale-110 ${
          isUser
            ? "bg-[var(--primary)] text-white"
            : "bg-[var(--canvas-soft)] text-[var(--ink)]"
        }`}
      >
        {isUser ? <User className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div className="max-w-[80%]">
        {isUser && timestamp ? (
          <span className="mb-1 block text-right text-[0.6rem] text-[var(--muted)]">
            {formatTime(timestamp)}
          </span>
        ) : null}
        <div
          className={`rounded-lg px-4 py-2.5 text-sm ${
            isUser
              ? "bg-[var(--primary)] text-white"
              : "bg-[var(--canvas-soft)] text-[var(--ink)]"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap leading-relaxed">{content}</p>
          ) : (
            <MarkdownContent content={content} isStreaming={isStreaming} />
          )}
        </div>
      </div>
    </div>
  );
}

function formatTime(iso: string): string {
  try {
    const date = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60_000);
    if (diffMin < 1) return "刚刚";
    if (diffMin < 60) return `${diffMin} 分钟前`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr} 小时前`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay} 天前`;
    return date.toLocaleDateString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}
