"use client";

import { MessageSquarePlus, Search, Trash2, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
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
  const deleteTarget = items.find((item) => item.session_id === confirming);

  const filtered = search.trim()
    ? items.filter((item) =>
        item.title.toLowerCase().includes(search.toLowerCase()),
      )
    : items;

  const statusIcons: Record<string, string> = {
    active: "bg-[var(--success)]",
    archived: "bg-[var(--muted)]",
    processing: "bg-[var(--primary)] animate-pulse",
  };
  /** Only show status dot + label for the currently active session. */
  function statusForSession(sessionId: string, status: string) {
    if (sessionId === activeId && status === "active") {
      return { dot: statusIcons.active, label: "进行中" };
    }
    // Inactive sessions don't need a status badge.
    return null;
  }

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-hidden border-r border-[var(--hairline)] bg-[var(--surface-inset)]">
      {/* New session header */}
      <div className="flex h-12 shrink-0 items-center gap-1 border-b border-[var(--hairline)] px-2.5">
        <Button
          className="h-8 flex-1 text-xs"
          onClick={onCreate}
          variant="ghost"
        >
          <MessageSquarePlus className="size-3.5" />
          新建对话
        </Button>
      </div>

      {/* Search */}
      <div className="shrink-0 px-2.5 pt-2.5">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-[var(--muted)]" />
          <Input
            aria-label="搜索会话"
            className="h-8 w-full border-[var(--hairline)] bg-[var(--surface)] pl-7 text-xs"
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索会话…"
            value={search}
          />
        </div>
      </div>

      {/* Session list */}
      <div
        aria-label="会话历史"
        className="min-h-0 flex-1 overflow-y-auto px-2 py-2.5"
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
          const sessionStatus = statusForSession(item.session_id, item.status);
          return (
            <div className="group relative mb-1" key={item.session_id}>
              <button
                aria-label={item.title}
                className={`min-h-9 w-full rounded-[var(--radius-md)] px-3 py-2 pr-9 text-left text-sm transition-colors ${
                  activeId === item.session_id
                    ? "bg-[var(--primary-subtle)] font-medium text-[var(--primary)]"
                    : "text-[var(--body)] hover:bg-[var(--surface)]/75 hover:text-[var(--ink)]"
                }`}
                onClick={() => onSelect(item.session_id)}
                type="button"
              >
                <span className="block truncate pr-1">{item.title}</span>
                {sessionStatus ? (
                  <span className="mt-1 flex items-center gap-1.5 text-xs text-[var(--muted)]">
                    <span
                      className={`inline-block size-1.5 shrink-0 rounded-full ${sessionStatus.dot}`}
                    />
                    {sessionStatus.label}
                  </span>
                ) : null}
              </button>

              {/* Delete button */}
              <button
                aria-label={`删除 ${item.title}`}
                className="absolute right-1 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-lg text-[var(--muted)] opacity-0 transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--danger)] focus:opacity-100 group-hover:opacity-100 max-[760px]:opacity-100"
                onClick={(event) => {
                  event.stopPropagation();
                  setConfirming(item.session_id);
                }}
                title="删除会话"
                type="button"
              >
                <Trash2 aria-hidden="true" className="size-3.5" />
              </button>
            </div>
          );
        })}
      </div>

      <Dialog
        onOpenChange={(open) => {
          if (!open) setConfirming(null);
        }}
        open={Boolean(deleteTarget)}
      >
        <DialogContent className="max-w-md">
          <DialogTitle>删除对话？</DialogTitle>
          <DialogDescription>
            此操作将永久删除“{deleteTarget?.title}”，且无法撤销。
          </DialogDescription>
          <div className="mt-6 flex justify-end gap-2">
            <Button onClick={() => setConfirming(null)} variant="secondary">
              取消
            </Button>
            <button
              className="inline-flex h-9 items-center justify-center rounded-[var(--radius-md)] bg-[var(--danger)] px-4 text-sm font-medium text-[var(--on-primary)] hover:opacity-90"
              onClick={() => {
                if (!deleteTarget) return;
                onDelete(deleteTarget.session_id);
                setConfirming(null);
              }}
              type="button"
            >
              删除
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </aside>
  );
}
