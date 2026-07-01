"use client";

import { Search, MessageSquarePlus, Trash2, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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
  const [search, setSearch] = useState("");
  const [confirming, setConfirming] = useState<string | null>(null);

  const filtered = search.trim()
    ? items.filter((item) =>
        item.title.toLowerCase().includes(search.toLowerCase()),
      )
    : items;

  const statusIcons: Record<string, string> = {
    active: "bg-green-400",
    archived: "bg-[var(--muted)]",
    processing: "bg-[var(--primary)] animate-pulse",
  };
  const statusLabels: Record<string, string> = {
    active: "进行中",
    archived: "已归档",
    processing: "处理中",
  };

  return (
    <aside className="flex min-h-0 flex-col overflow-hidden border-r border-[var(--hairline)] bg-[var(--surface)]">
      {/* New session button */}
      <div className="shrink-0 border-b border-[var(--hairline)] p-3">
        <Button className="w-full" onClick={onCreate} variant="secondary">
          <MessageSquarePlus className="size-4" />
          新建对话
        </Button>
      </div>

      {/* Search */}
      <div className="shrink-0 px-3 pt-2">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-[var(--muted)]" />
          <Input
            aria-label="搜索会话"
            className="h-8 w-full pl-7 text-xs"
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索会话…"
            value={search}
          />
        </div>
      </div>

      {/* Session list */}
      <div
        aria-label="会话历史"
        className="min-h-0 flex-1 overflow-y-auto p-2"
      >
        {loading ? (
          <div className="flex items-center gap-2 p-2">
            <Loader2 className="size-3.5 animate-spin text-[var(--muted)]" />
            <p className="text-xs text-[var(--muted)]">正在加载会话…</p>
          </div>
        ) : null}
        {!loading && filtered.length === 0 ? (
          <p className="p-2 text-xs text-[var(--muted)]">
            {search ? "没有匹配的会话" : "暂无历史会话"}
          </p>
        ) : null}
        {filtered.map((item) => {
          const statusLabel = statusLabels[item.status] ?? item.status;
          const statusDot = statusIcons[item.status] ?? "bg-[var(--muted)]";
          return (
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
                <span className="block truncate pr-1">{item.title}</span>
                <span className="mt-1 flex items-center gap-1.5 text-xs text-[var(--muted)]">
                  <span
                    className={`inline-block size-1.5 shrink-0 rounded-full ${statusDot}`}
                  />
                  {statusLabel}
                </span>
              </button>

              {/* Delete button */}
              {confirming === item.session_id ? (
                <div className="absolute bottom-1.5 right-1.5 flex items-center gap-1 rounded bg-[var(--surface)] p-1 shadow-[var(--shadow-md)]">
                  <span className="ml-1 text-[0.6rem] text-[var(--danger)]">
                    确认删除？
                  </span>
                  <button
                    className="rounded px-1.5 py-0.5 text-[0.6rem] font-medium text-[var(--danger)] hover:bg-[var(--danger-subtle)]"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(item.session_id);
                      setConfirming(null);
                    }}
                    type="button"
                  >
                    删除
                  </button>
                  <button
                    className="rounded px-1.5 py-0.5 text-[0.6rem] text-[var(--muted)] hover:bg-[var(--canvas-soft)]"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConfirming(null);
                    }}
                    type="button"
                  >
                    取消
                  </button>
                </div>
              ) : (
                <button
                  aria-label={`删除 ${item.title}`}
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-[var(--radius-sm)] p-1 text-[var(--muted)] opacity-0 transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--danger)] group-hover:opacity-100"
                  onClick={(event) => {
                    event.stopPropagation();
                    setConfirming(item.session_id);
                  }}
                  title="删除会话"
                  type="button"
                >
                  <Trash2 aria-hidden="true" className="size-3.5" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
