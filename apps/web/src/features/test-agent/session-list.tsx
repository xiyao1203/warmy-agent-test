import { MessageSquarePlus } from "lucide-react";

import { Button } from "@/components/ui/button";

import type { SessionSummary } from "./api";

export function SessionList({
  activeId,
  items,
  loading,
  onCreate,
  onSelect,
}: {
  activeId: string | null;
  items: SessionSummary[];
  loading: boolean;
  onCreate: () => void;
  onSelect: (id: string) => void;
}) {
  return (
    <aside className="flex min-h-0 flex-col border-r border-[var(--border)] bg-[var(--surface)]">
      <div className="border-b border-[var(--border)] p-3">
        <Button className="w-full" onClick={onCreate} variant="secondary">
          <MessageSquarePlus className="size-4" />
          新建对话
        </Button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2" aria-label="会话历史">
        {loading ? <p className="p-2 text-xs text-[var(--text-muted)]">正在加载会话…</p> : null}
        {!loading && items.length === 0 ? (
          <p className="p-2 text-xs text-[var(--text-muted)]">暂无历史会话</p>
        ) : null}
        {items.map((item) => (
          <button
            aria-label={item.title}
            className={`mb-1 w-full rounded-[var(--radius-sm)] px-3 py-2 text-left text-sm transition-colors ${
              activeId === item.session_id
                ? "bg-[var(--accent-subtle)] text-[var(--accent)]"
                : "hover:bg-[var(--surface-subtle)]"
            }`}
            key={item.session_id}
            onClick={() => onSelect(item.session_id)}
            type="button"
          >
            <span className="block truncate">{item.title}</span>
            <span className="mt-1 block text-xs text-[var(--text-muted)]">{item.status}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}
