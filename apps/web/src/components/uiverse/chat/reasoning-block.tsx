"use client";

import { useState } from "react";

import { Brain, ChevronDown } from "lucide-react";

export function ReasoningBlock({
  content,
  step,
  total,
  capability,
  isStreaming,
}: {
  content: string;
  step: number;
  total: number;
  capability: string;
  isStreaming?: boolean;
}) {
  const [open, setOpen] = useState(isStreaming ?? false);

  // Auto-open when streaming
  const openState = isStreaming ? true : open;

  return (
    <div className="my-1.5 animate-fadeIn overflow-hidden rounded-[var(--radius-md)] border border-purple-200/60 bg-purple-50/40 dark:border-purple-800/30 dark:bg-purple-950/20">
      <button
        className="flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-purple-100/50 dark:hover:bg-purple-900/20"
        onClick={() => setOpen((v) => !v)}
        type="button"
      >
        <span className="flex size-5 shrink-0 items-center justify-center rounded bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400">
          <Brain className={`size-3 ${isStreaming ? "animate-pulse" : openState ? "" : "animate-pulse"}`} />
        </span>
        <span className="min-w-0 flex-1 text-[0.7rem] font-medium text-purple-700 dark:text-purple-300">
          {isStreaming ? "分析中…" : `思考 · Step ${step}/${total}`}
        </span>
        <span className="hidden truncate text-[0.65rem] text-purple-500/70 sm:inline">
          {capability}
        </span>
        <ChevronDown
          className={`size-3 shrink-0 text-purple-400 transition-transform duration-200 ${
            openState ? "rotate-180" : ""
          }`}
        />
      </button>
      {openState ? (
        <div className="border-t border-purple-200/50 px-3 py-2.5 dark:border-purple-800/20">
          <p className="whitespace-pre-wrap text-xs leading-relaxed text-[var(--muted)]">
            {content}
            {isStreaming ? (
              <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-purple-400 align-middle" />
            ) : null}
          </p>
        </div>
      ) : null}
    </div>
  );
}

