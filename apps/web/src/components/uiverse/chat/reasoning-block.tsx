"use client";

import { Brain, ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export function ReasoningBlock({
  content,
  step,
  total,
  capability,
  isStreaming,
}: {
  content: string;
  step?: number;
  total?: number;
  capability?: string;
  isStreaming?: boolean;
}) {
  const [open, setOpen] = useState(true);
  const wasStreaming = useRef(isStreaming);

  // Auto-collapse 600ms after streaming ends (Codex-style)
  useEffect(() => {
    if (wasStreaming.current && !isStreaming) {
      const timer = setTimeout(() => setOpen(false), 600);
      return () => clearTimeout(timer);
    }
    wasStreaming.current = isStreaming;
  }, [isStreaming]);

  const isOpen = isStreaming ? true : open;
  const hasStep = step !== undefined && total !== undefined && total > 0;

  return (
    <div className="my-1 animate-fadeIn overflow-hidden rounded-lg border border-[var(--hairline)] bg-[var(--canvas-soft)]/60 transition-colors">
      <button
        aria-expanded={isOpen}
        className="flex w-full items-center gap-2 px-3 py-1.5 text-left transition-colors hover:bg-[var(--canvas-soft)]"
        onClick={() => setOpen((v) => !v)}
        type="button"
      >
        <span className="flex size-4 shrink-0 items-center justify-center text-[var(--muted)]">
          <Brain className={`size-3 ${isStreaming ? "animate-pulse" : ""}`} />
        </span>
        <span className="min-w-0 flex-1 truncate text-[0.7rem] text-[var(--muted)]">
          {isStreaming
            ? "思考中…"
            : hasStep
              ? `思考 · Step ${step}/${total}`
              : "思考"}
        </span>
        {capability ? (
          <span className="hidden truncate text-[0.65rem] text-[var(--muted)]/60 sm:inline">
            {capability}
          </span>
        ) : null}
        <ChevronDown
          className={`size-3 shrink-0 text-[var(--muted)]/50 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>
      <div
        className={`grid transition-all duration-300 ease-out ${
          isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        }`}
      >
        <div className="overflow-hidden">
          <div className="border-t border-[var(--hairline)] px-3 py-2">
            <p className="whitespace-pre-wrap text-[0.75rem] leading-relaxed text-[var(--muted)]">
              {content}
              {isStreaming ? (
                <span className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-[var(--ink)]/30 align-middle" />
              ) : null}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
