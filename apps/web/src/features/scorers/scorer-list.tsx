"use client";

import { Pencil, Plus, ToggleLeft, ToggleRight, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import type { ScorerItem } from "./api";
import { deleteScorer, listScorers, updateScorer } from "./api";
import { ScorerEditorDialog } from "./scorer-editor";

const TYPE_LABELS: Record<string, string> = {
  rule: "规则",
  model: "模型",
  reference: "参考",
};

export function ScorerList({ projectId }: { projectId: string }) {
  const [scorers, setScorers] = useState<ScorerItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editItem, setEditItem] = useState<ScorerItem | undefined>();

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setScorers(await listScorers(projectId));
    } catch {
      setError("加载评分器列表失败");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    let active = true;
    void listScorers(projectId)
      .then((items) => {
        if (active) setScorers(items);
      })
      .catch(() => {
        if (active) setError("加载评分器列表失败");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  async function handleToggle(item: ScorerItem) {
    await updateScorer(projectId, item.id, { enabled: !item.enabled });
    await reload();
  }

  async function handleDelete(id: string) {
    if (!confirm("确定删除此评分器？")) return;
    await deleteScorer(projectId, id);
    await reload();
  }

  if (loading) {
    return (
      <div className="grid min-h-[40vh] place-items-center text-sm text-[var(--muted)]">
        正在加载评分器…
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">评分器</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            管理项目的评分器配置，用于运行结果的多维度评估。
          </p>
        </div>
        <Button
          onClick={() => {
            setEditItem(undefined);
            setEditorOpen(true);
          }}
          variant="primary"
        >
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建评分器
        </Button>
      </header>

      {error ? (
        <p className="mt-4 text-sm text-[var(--danger)]">{error}</p>
      ) : null}

      {scorers.length === 0 ? (
        <div className="mt-8 rounded-[var(--radius-lg)] border border-dashed border-[var(--hairline)] p-10 text-center">
          <p className="text-sm font-medium text-[var(--muted)]">
            暂无评分器
          </p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            点击「创建评分器」开始配置。
          </p>
        </div>
      ) : (
        <ul className="mt-5 space-y-3">
          {scorers.map((s) => (
            <li
              className="flex items-center justify-between gap-4 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-5 py-4"
              key={s.id}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold">{s.name}</h2>
                  <Badge>{TYPE_LABELS[s.scorer_type] ?? s.scorer_type}</Badge>
                  {!s.enabled ? <Badge tone="warning">已禁用</Badge> : null}
                </div>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  权重 {s.weight} · 阈值 {s.threshold}
                  {s.description ? ` · ${s.description}` : ""}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                <Button
                  aria-label={s.enabled ? "禁用" : "启用"}
                  onClick={() => handleToggle(s)}
                  variant="ghost"
                >
                  {s.enabled ? (
                    <ToggleRight
                      aria-hidden="true"
                      className="size-4 text-[var(--success)]"
                    />
                  ) : (
                    <ToggleLeft
                      aria-hidden="true"
                      className="size-4 text-[var(--muted)]"
                    />
                  )}
                </Button>
                <Button
                  aria-label="编辑"
                  onClick={() => {
                    setEditItem(s);
                    setEditorOpen(true);
                  }}
                  variant="ghost"
                >
                  <Pencil aria-hidden="true" className="size-4" />
                </Button>
                <Button
                  aria-label="删除"
                  onClick={() => handleDelete(s.id)}
                  variant="ghost"
                >
                  <Trash2
                    aria-hidden="true"
                    className="size-4 text-[var(--danger)]"
                  />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <ScorerEditorDialog
        onSaved={reload}
        open={editorOpen}
        projectId={projectId}
        scorer={editItem}
        onOpenChange={setEditorOpen}
      />
    </div>
  );
}
