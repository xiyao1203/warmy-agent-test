"use client";

import { Bot, Check, Copy, ThumbsDown, ThumbsUp, User } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

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
  const [copied, setCopied] = useState(false);
  const [rated, setRated] = useState<"up" | "down" | null>(null);
  const isUser = role === "user";

  useEffect(() => {
    if (animate) {
      const timer = setTimeout(() => setVisible(true), 50);
      return () => clearTimeout(timer);
    }
  }, [animate]);

  const handleCopy = useCallback(() => {
    void navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [content]);

  return (
    <div
      className={`flex gap-4 transition-all duration-300 ${
        isUser ? "flex-row-reverse" : ""
      } ${visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"}`}
    >
      <div
        className={`flex size-7 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-[var(--primary)] text-white"
            : "border border-[var(--hairline)] bg-white text-[var(--ink)]"
        }`}
      >
        {isUser ? <User className="size-3.5" /> : <Bot className="size-3.5" />}
      </div>
      <div className="min-w-0 max-w-[85%]">
        {timestamp ? (
          <span
            className={`mb-0.5 block text-[0.65rem] text-[var(--muted)] ${
              isUser ? "text-right" : "text-left"
            }`}
          >
            {formatTime(timestamp)}
          </span>
        ) : null}
        <div
          className={`group/bubble relative text-[0.9375rem] leading-7 ${
            isUser
              ? "rounded-2xl rounded-br-md bg-[var(--primary)] px-4 py-2.5 text-white"
              : "text-[var(--ink)]"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <MarkdownContent content={content} isStreaming={isStreaming} />
          )}
          {/* Hover controls — copy + feedback */}
          {!isStreaming ? (
            <div
              className={`absolute flex gap-0.5 opacity-0 transition-all group-hover/bubble:opacity-100 ${
                isUser
                  ? "-left-9 top-1/2 -translate-y-1/2"
                  : "-bottom-7 right-0"
              }`}
            >
              {/* Copy */}
              <button
                aria-label={copied ? "已复制" : "复制消息"}
                className="rounded-md p-1 text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
                onClick={handleCopy}
                type="button"
              >
                {copied ? (
                  <Check className="size-3.5 text-[var(--success)]" />
                ) : (
                  <Copy className="size-3.5" />
                )}
              </button>
              {/* Feedback — assistant only */}
              {!isUser ? (
                <>
                  <button
                    aria-label="有帮助"
                    className={`rounded-md p-1 transition-colors ${
                      rated === "up"
                        ? "text-[var(--success)]"
                        : "text-[var(--muted)] hover:text-[var(--ink)]"
                    }`}
                    onClick={() => setRated(rated === "up" ? null : "up")}
                    type="button"
                  >
                    <ThumbsUp className="size-3.5" />
                  </button>
                  <button
                    aria-label="无帮助"
                    className={`rounded-md p-1 transition-colors ${
                      rated === "down"
                        ? "text-[var(--danger)]"
                        : "text-[var(--muted)] hover:text-[var(--ink)]"
                    }`}
                    onClick={() => setRated(rated === "down" ? null : "down")}
                    type="button"
                  >
                    <ThumbsDown className="size-3.5" />
                  </button>
                </>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function formatTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
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
}
