"use client";

import {
  Bot,
  Check,
  Copy,
  Pencil,
  RefreshCw,
  ThumbsDown,
  ThumbsUp,
  User,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { MarkdownContent } from "./markdown-content";

type MessageBubbleProps = {
  content: string;
  role: "assistant" | "user";
  animate?: boolean;
  isStreaming?: boolean;
  timestamp?: string;
  isLastAssistant?: boolean;
  onRegenerate?: () => void;
  onEdit?: (newContent: string) => void;
};

export function MessageBubble({
  animate = true,
  content,
  isLastAssistant = false,
  isStreaming = false,
  onEdit,
  onRegenerate,
  role,
  timestamp,
}: MessageBubbleProps) {
  const [visible, setVisible] = useState(!animate);
  const [copied, setCopied] = useState(false);
  const [rated, setRated] = useState<"up" | "down" | null>(null);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(content);
  const editInputRef = useRef<HTMLTextAreaElement>(null);
  const isUser = role === "user";

  useEffect(() => {
    if (animate) {
      const timer = setTimeout(() => setVisible(true), 50);
      return () => clearTimeout(timer);
    }
  }, [animate]);

  useEffect(() => {
    if (editing && editInputRef.current) {
      editInputRef.current.focus();
    }
  }, [editing]);

  const handleCopy = useCallback(() => {
    void navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [content]);

  const handleEditSubmit = useCallback(() => {
    const trimmed = editText.trim();
    if (trimmed && trimmed !== content) {
      onEdit?.(trimmed);
    }
    setEditing(false);
  }, [editText, content, onEdit]);

  const handleEditKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleEditSubmit();
      }
      if (e.key === "Escape") {
        setEditText(content);
        setEditing(false);
      }
    },
    [handleEditSubmit, content],
  );

  return (
    <div
      className={`flex gap-4 transition-all duration-300 ${
        isUser ? "flex-row-reverse" : ""
      } ${visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"}`}
    >
      <div
        className={`flex size-7 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-[var(--primary)] text-[var(--on-primary)]"
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
              ? "rounded-[var(--radius-lg)] rounded-br-[var(--radius-sm)] bg-[var(--primary)] px-4 py-2.5 text-[var(--on-primary)]"
              : "text-[var(--ink)]"
          }`}
        >
          {isUser ? (
            editing ? (
              <div className="flex flex-col gap-2">
                <textarea
                  ref={editInputRef}
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  onKeyDown={handleEditKeyDown}
                  className="w-full resize-none rounded-xl border border-[var(--hairline)] bg-white/90 px-3 py-2 text-sm text-[var(--ink)] outline-none focus:border-[var(--primary)] min-h-[2.5rem]"
                  rows={2}
                />
                <div className="flex items-center justify-end gap-1 text-[0.7rem] text-[var(--on-primary)] opacity-60">
                  <span>Enter 提交 · Esc 取消</span>
                  <button
                    onClick={handleEditSubmit}
                    className="rounded-md bg-white/20 px-2 py-0.5 transition-colors hover:bg-white/30"
                    type="button"
                  >
                    确认
                  </button>
                </div>
              </div>
            ) : (
              <p className="whitespace-pre-wrap">{content}</p>
            )
          ) : (
            <MarkdownContent content={content} isStreaming={isStreaming} />
          )}
          {/* Hover controls — copy + feedback + edit + regenerate */}
          {!isStreaming ? (
            <div
              className={`mt-1 flex gap-0.5 invisible opacity-0 group-hover/bubble:visible group-hover/bubble:opacity-100 transition-all ${
                isUser ? "justify-end" : "justify-start"
              }`}
              aria-label="消息操作"
            >
              {/* Copy */}
              <button
                aria-label={copied ? "已复制" : "复制消息"}
                className="rounded-md p-1.5 text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
                onClick={handleCopy}
                type="button"
              >
                {copied ? (
                  <Check className="size-3.5 text-[var(--success)]" />
                ) : (
                  <Copy className="size-3.5" />
                )}
              </button>
              {/* Edit — user messages only */}
              {isUser && onEdit && !editing ? (
                <button
                  aria-label="编辑消息"
                  className="rounded-md p-1.5 text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
                  onClick={() => {
                    setEditText(content);
                    setEditing(true);
                  }}
                  type="button"
                >
                  <Pencil className="size-3.5" />
                </button>
              ) : null}
              {/* Feedback — assistant only */}
              {!isUser ? (
                <>
                  <button
                    aria-label="有帮助"
                    className={`rounded-md p-1.5 transition-colors ${
                      rated === "up"
                        ? "text-[var(--success)]"
                        : "text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
                    }`}
                    onClick={() => setRated(rated === "up" ? null : "up")}
                    type="button"
                  >
                    <ThumbsUp className="size-3.5" />
                  </button>
                  <button
                    aria-label="无帮助"
                    className={`rounded-md p-1.5 transition-colors ${
                      rated === "down"
                        ? "text-[var(--danger)]"
                        : "text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
                    }`}
                    onClick={() => setRated(rated === "down" ? null : "down")}
                    type="button"
                  >
                    <ThumbsDown className="size-3.5" />
                  </button>
                </>
              ) : null}
              {/* Regenerate — last assistant message only */}
              {!isUser && isLastAssistant && onRegenerate ? (
                <button
                  aria-label="重新生成回复"
                  className="rounded-md p-1.5 text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
                  onClick={() => onRegenerate()}
                  type="button"
                >
                  <RefreshCw className="size-3.5" />
                </button>
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
  return date.toLocaleDateString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
