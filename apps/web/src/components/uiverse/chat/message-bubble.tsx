"use client";

import { Bot, User } from "lucide-react";
import { useEffect, useState } from "react";

type MessageBubbleProps = {
  content: string;
  role: "assistant" | "user";
  animate?: boolean;
};

export function MessageBubble({
  animate = true,
  content,
  role,
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
            ? "bg-[var(--accent)] text-white"
            : "bg-[var(--surface-subtle)] text-[var(--text)]"
        }`}
      >
        {isUser ? <User className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
          isUser
            ? "bg-[var(--accent)] text-white"
            : "bg-[var(--surface-subtle)] text-[var(--text)]"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
