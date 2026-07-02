"use client";

import { ChevronRight } from "lucide-react";

export function FollowUpChips({
  items,
  onClick,
}: {
  items: string[];
  onClick: (text: string) => void;
}) {
  if (items.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2 pl-11 animate-fadeIn">
      {items.map((text) => (
        <button
          className="inline-flex items-center gap-1 rounded-full border border-[var(--hairline)] bg-[var(--surface)] px-3 py-1.5 text-[0.75rem] leading-none text-[var(--muted)] transition-all hover:border-[var(--primary)]/30 hover:bg-[var(--primary)]/5 hover:text-[var(--primary)]"
          key={text}
          onClick={() => onClick(text)}
          type="button"
        >
          {text}
          <ChevronRight className="size-3" />
        </button>
      ))}
    </div>
  );
}
