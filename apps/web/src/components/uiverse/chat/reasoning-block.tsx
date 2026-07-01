"use client";

import { useState } from "react";

import { Brain, ChevronDown } from "lucide-react";

export function ReasoningBlock({
  content,
  step,
  total,
  capability,
}: {
  content: string;
  step: number;
  total: number;
  capability: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="my-1.5 animate-fadeIn overflow-hidden rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--canvas-soft)]/50">
      <button
        className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left transition-colors hover:bg-[var(--canvas-soft)]"
        onClick={() => setOpen((v) => !v)}
        type="button"
      >
        <span className="flex size-6 shrink-0 items-center justify-center rounded bg-purple-100 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400">
          <Brain className="size-3.5" />
        </span>
        <span className="min-w-0 flex-1 text-xs font-medium text-[var(--ink)]">
          {step}/{total} 思考：{capability}
        </span>
        <ChevronDown
          className={`size-3.5 shrink-0 text-[var(--muted)] transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>
      {open ? (
        <div className="border-t border-[var(--hairline)] px-3 py-2.5">
          <p className="whitespace-pre-wrap text-xs leading-relaxed text-[var(--muted)]">
            {content}
          </p>
        </div>
      ) : null}
    </div>
  );
}

