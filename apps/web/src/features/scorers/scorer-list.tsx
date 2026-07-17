"use client";

import {
  ClipboardCheck,
  FlaskConical,
  Pencil,
  PlayCircle,
  Plus,
  Scale,
  ToggleLeft,
  ToggleRight,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ResourceReferenceLink } from "@/components/ui/resource-reference-link";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";

import { Skeleton } from "@/components/uiverse";
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
  const [deleteTarget, setDeleteTarget] = useState<ScorerItem | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

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
    setDeleteBusy(true);
    try {
      await deleteScorer(projectId, id);
      setDeleteTarget(null);
      await reload();
    } finally {
      setDeleteBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="workspace-page">
        <header className="border-b border-[var(--hairline)] pb-5">
          <Skeleton className="h-7 w-32" />
          <Skeleton className="mt-2 h-4 w-72" />
        </header>
        <div className="mt-5 space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton
              className="h-16 w-full rounded-[var(--radius-lg)]"
              key={i}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="workspace-page">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">评分器</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            创建评分规则，测试计划选择后，运行结果会自动产出评分并用于实验对比。
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
          新建评分器
        </Button>
      </header>

      <section className="mt-5 grid gap-3 md:grid-cols-4">
        <FlowCard
          description="规则、参考答案或模型评分"
          icon={<Scale aria-hidden="true" className="size-4" />}
          label="1. 新建评分器"
        />
        <FlowCard
          description="在评估设置中选择"
          href={`/projects/${projectId}/test-plans`}
          icon={<ClipboardCheck aria-hidden="true" className="size-4" />}
          label="2. 配置测试计划"
        />
        <FlowCard
          description="运行后自动生成分数"
          href={`/projects/${projectId}/runs`}
          icon={<PlayCircle aria-hidden="true" className="size-4" />}
          label="3. 查看评分结果"
        />
        <FlowCard
          description="对比两次运行的提升和退化"
          href={`/projects/${projectId}/experiments`}
          icon={<FlaskConical aria-hidden="true" className="size-4" />}
          label="4. 做实验对比"
        />
      </section>

      {error ? (
        <p className="mt-4 text-sm text-[var(--danger)]">{error}</p>
      ) : null}

      {scorers.length === 0 ? (
        <div className="mt-6 rounded-[var(--radius-lg)] border border-dashed border-[var(--hairline)] p-10 text-center">
          <p className="text-sm font-medium text-[var(--muted)]">暂无评分器</p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            先新建评分器，再到测试计划的评估设置中选择它。
          </p>
          <div className="mt-4 flex justify-center gap-2">
            <Button
              onClick={() => {
                setEditItem(undefined);
                setEditorOpen(true);
              }}
              variant="primary"
            >
              <Plus aria-hidden="true" className="mr-1.5 size-4" />
              新建评分器
            </Button>
            <Button asChild variant="secondary">
              <Link href={`/projects/${projectId}/test-plans`}>
                去配置测试计划
              </Link>
            </Button>
          </div>
        </div>
      ) : (
        <ul className="mt-6 space-y-3">
          {scorers.map((s) => (
            <li
              className="flex items-center justify-between gap-4 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-5 py-4"
              key={s.id}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold">{s.name}</h2>
                  <Badge>{TYPE_LABELS[s.scorer_type] ?? s.scorer_type}</Badge>
                  {s.latest_published_version_number ? (
                    <Badge tone="success">
                      可用于计划 v{s.latest_published_version_number}
                    </Badge>
                  ) : (
                    <Badge tone="warning">待保存版本</Badge>
                  )}
                  {!s.enabled ? <Badge tone="warning">已禁用</Badge> : null}
                </div>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  权重 {s.weight} · 阈值 {s.threshold}
                  {s.description ? ` · ${s.description}` : ""}
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[var(--muted)]">
                  <span>
                    最新版本：
                    <ResourceReferenceLink reference={s.latest_version} />
                  </span>
                  <span>引用次数 {s.usage_count ?? 0}</span>
                  <span>
                    最近校准{" "}
                    {s.last_calibrated_at
                      ? new Date(s.last_calibrated_at).toLocaleString("zh-CN")
                      : "暂无数据"}
                  </span>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                <Button asChild className="px-3" variant="secondary">
                  <Link href={`/projects/${projectId}/test-plans`}>
                    配置计划
                  </Link>
                </Button>
                <Button
                  aria-label={s.enabled ? `禁用${s.name}` : `启用${s.name}`}
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
                  aria-label={`设置${s.name}`}
                  onClick={() => {
                    setEditItem(s);
                    setEditorOpen(true);
                  }}
                  variant="ghost"
                >
                  <Pencil aria-hidden="true" className="size-4" />
                </Button>
                <Button
                  aria-label={`删除${s.name}`}
                  onClick={() => setDeleteTarget(s)}
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

      <Dialog
        onOpenChange={() => setDeleteTarget(null)}
        open={deleteTarget !== null}
      >
        <DialogContent>
          <DialogTitle>确认删除</DialogTitle>
          <DialogDescription>
            确定要删除评分器「{deleteTarget?.name}」吗？此操作不可撤销。
          </DialogDescription>
          <div className="mt-5 flex justify-end gap-3">
            <Button onClick={() => setDeleteTarget(null)} variant="secondary">
              取消
            </Button>
            <Button
              loading={deleteBusy}
              onClick={() => {
                if (deleteTarget) void handleDelete(deleteTarget.id);
              }}
              variant="danger"
            >
              确认删除
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function FlowCard({
  description,
  href,
  icon,
  label,
}: {
  description: string;
  href?: string;
  icon: ReactNode;
  label: string;
}) {
  const content = (
    <>
      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)]">
        {icon}
      </span>
      <span className="min-w-0">
        <span className="block font-medium">{label}</span>
        <span className="block truncate text-xs text-[var(--muted)]">
          {description}
        </span>
      </span>
    </>
  );

  if (href) {
    return (
      <Link
        className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm transition-colors hover:border-[var(--primary)]"
        href={href}
      >
        {content}
      </Link>
    );
  }

  return (
    <div className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm">
      {content}
    </div>
  );
}
