import { MessageSquarePlus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";

import type { SessionSummary } from "./api";

export function SessionList({
  activeId,
  items,
  loading,
  onCreate,
  onDelete,
  onSelect,
}: {
  activeId: string | null;
  items: SessionSummary[];
  loading: boolean;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onSelect: (id: string) => void;
}) {
  return (
    <aside className="flex min-h-0 flex-col overflow-hidden border-r border-[var(--hairline)] bg-[var(--surface)]">
      <div className="shrink-0 border-b border-[var(--hairline)] p-3">
        <Button className="w-full" onClick={onCreate} variant="secondary">
          <MessageSquarePlus className="size-4" />
          新建对话
        </Button>
      </div>
      <div aria-label="会话历史" className="min-h-0 flex-1 overflow-y-auto p-2">
        {loading ? (
          <p className="p-2 text-xs text-[var(--muted)]">正在加载会话…</p>
        ) : null}
        {!loading && items.length === 0 ? (
          <p className="p-2 text-xs text-[var(--muted)]">暂无历史会话</p>
        ) : null}
        {items.map((item) => (
          <div className="group relative mb-1" key={item.session_id}>
            <button
              aria-label={item.title}
              className={`w-full rounded-[var(--radius-md)] py-2 pl-3 pr-8 text-left text-sm transition-colors ${
                activeId === item.session_id
                  ? "bg-[var(--primary-subtle)] text-[var(--primary)]"
                  : "hover:bg-[var(--canvas-soft)]"
              }`}
              onClick={() => onSelect(item.session_id)}
              type="button"
            >
              <span className="block truncate">{item.title}</span>
              <span className="mt-1 block text-xs text-[var(--muted)]">
                {item.status}
              </span>
            </button>
            <button
              aria-label={`删除 ${item.title}`}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-[var(--radius-sm)] p-1 text-[var(--muted)] opacity-0 transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--danger)] group-hover:opacity-100"
              onClick={(event) => {
                event.stopPropagation();
                onDelete(item.session_id);
              }}
              title="删除会话"
              type="button"
            >
              <Trash2 aria-hidden="true" className="size-3.5" />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
