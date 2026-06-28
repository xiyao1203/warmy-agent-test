"use client";

import {
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Equal,
  SkipForward,
  ThumbsDown,
  ThumbsUp,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import type { ReviewTask } from "./api";
import { listReviews, scoreReview, rejectReview, skipReview } from "./api";

const STATUS_TONES: Record<
  string,
  "success" | "warning" | "danger" | "neutral"
> = {
  pending: "warning",
  approved: "success",
  rejected: "danger",
  skipped: "neutral",
};

export function ReviewWorkbench({ projectId }: { projectId: string }) {
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ReviewTask | null>(null);
  const [filter, setFilter] = useState<string>("pending");
  const [score, setScore] = useState(0.8);
  const [opinion, setOpinion] = useState("");
  const [acting, setActing] = useState(false);
  const [reviewMode, setReviewMode] = useState<"score" | "ab_preference">(
    "score",
  );
  const [abPreference, setAbPreference] = useState<"a" | "b" | "equal" | null>(
    null,
  );

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setTasks(await listReviews(projectId, filter || undefined));
    } catch {
      /* empty */
    } finally {
      setLoading(false);
    }
  }, [projectId, filter]);

  useEffect(() => {
    let active = true;
    void listReviews(projectId, filter || undefined)
      .then((items) => {
        if (active) setTasks(items);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [filter, projectId]);

  async function handleApprove() {
    if (!selected) return;
    setActing(true);
    try {
      await scoreReview(projectId, selected.id, {
        score,
        opinion: opinion || undefined,
      });
      setSelected(null);
      setOpinion("");
      await reload();
    } finally {
      setActing(false);
    }
  }

  async function handleReject() {
    if (!selected) return;
    setActing(true);
    try {
      await rejectReview(projectId, selected.id, opinion || undefined);
      setSelected(null);
      setOpinion("");
      await reload();
    } finally {
      setActing(false);
    }
  }

  async function handleSkip(taskId: string) {
    setActing(true);
    try {
      await skipReview(projectId, taskId);
      if (selected?.id === taskId) setSelected(null);
      await reload();
    } finally {
      setActing(false);
    }
  }

  if (loading) {
    return (
      <div className="grid min-h-[40vh] place-items-center text-sm text-[var(--text-muted)]">
        正在加载审核任务…
      </div>
    );
  }

  const pendingCount = tasks.filter((t) => t.status === "pending").length;

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">人工审核</h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            {pendingCount > 0
              ? `${pendingCount} 个待审核任务`
              : "暂无待审核任务"}
          </p>
        </div>
        <div className="flex gap-2">
          {(["pending", "approved", "rejected", "skipped", ""] as const).map(
            (s) => (
              <Button
                key={s}
                onClick={() => setFilter(s)}
                variant={filter === s ? "primary" : "ghost"}
              >
                {s === ""
                  ? "全部"
                  : s === "pending"
                    ? "待审核"
                    : s === "approved"
                      ? "通过"
                      : s === "rejected"
                        ? "拒绝"
                        : "跳过"}
              </Button>
            ),
          )}
        </div>
      </header>

      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_24rem] gap-5 max-[1100px]:grid-cols-1">
        {/* 任务列表 */}
        <ul className="space-y-2">
          {tasks.length === 0 ? (
            <li className="rounded border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--text-muted)]">
              <ClipboardCheck className="mx-auto size-8" />
              <p className="mt-2">暂无审核任务</p>
            </li>
          ) : (
            tasks.map((t) => (
              <li key={t.id}>
                <button
                  className={`flex w-full items-center gap-3 rounded border px-4 py-3 text-left text-sm transition-colors ${
                    selected?.id === t.id
                      ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                      : "border-[var(--border)] hover:bg-[var(--surface-subtle)]"
                  }`}
                  onClick={() => setSelected(t)}
                  type="button"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-mono text-xs">
                      {t.run_case_id.slice(0, 12)}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                      置信度 {(t.confidence * 100).toFixed(0)}%
                      {t.score != null ? ` · 评分 ${t.score.toFixed(2)}` : ""}
                    </p>
                  </div>
                  <Badge tone={STATUS_TONES[t.status] ?? "neutral"}>
                    {t.status === "pending"
                      ? "待审核"
                      : t.status === "approved"
                        ? "通过"
                        : t.status === "rejected"
                          ? "拒绝"
                          : "跳过"}
                  </Badge>
                  {t.status === "pending" ? (
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        void handleSkip(t.id);
                      }}
                      variant="ghost"
                    >
                      <SkipForward className="size-4" />
                    </Button>
                  ) : null}
                  <ChevronRight className="size-4 text-[var(--text-muted)]" />
                </button>
              </li>
            ))
          )}
        </ul>

        {/* 详情 + 评分面板 */}
        <aside className="h-fit rounded border border-[var(--border)] bg-[var(--surface)] p-5">
          {selected ? (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-medium text-[var(--text-muted)]">
                  用例 ID
                </p>
                <p className="mt-1 font-mono text-sm">{selected.run_case_id}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-[var(--text-muted)]">置信度</p>
                  <p className="font-semibold">
                    {(selected.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-muted)]">状态</p>
                  <Badge tone={STATUS_TONES[selected.status] ?? "neutral"}>
                    {selected.status}
                  </Badge>
                </div>
                {selected.score != null ? (
                  <div>
                    <p className="text-xs text-[var(--text-muted)]">评分</p>
                    <p className="font-semibold">{selected.score.toFixed(2)}</p>
                  </div>
                ) : null}
                {selected.opinion ? (
                  <div className="col-span-2">
                    <p className="text-xs text-[var(--text-muted)]">审核意见</p>
                    <p className="mt-1 text-sm">{selected.opinion}</p>
                  </div>
                ) : null}
              </div>

              {selected.status === "pending" ? (
                <div className="border-t border-[var(--border)] pt-4">
                  {/* 审核模式切换 */}
                  <div className="mb-4 flex gap-2">
                    <Button
                      onClick={() => setReviewMode("score")}
                      variant={reviewMode === "score" ? "primary" : "ghost"}
                    >
                      评分模式
                    </Button>
                    <Button
                      onClick={() => setReviewMode("ab_preference")}
                      variant={
                        reviewMode === "ab_preference" ? "primary" : "ghost"
                      }
                    >
                      A/B 偏好
                    </Button>
                  </div>

                  {reviewMode === "score" ? (
                    /* 评分模式 */
                    <>
                      <label className="block text-sm font-medium">
                        评分（0-1）
                        <Input
                          className="mt-1.5"
                          max={1}
                          min={0}
                          onChange={(e) => setScore(Number(e.target.value))}
                          step={0.01}
                          type="number"
                          value={score}
                        />
                      </label>
                      <label className="mt-3 block text-sm font-medium">
                        审核意见
                        <Input
                          className="mt-1.5"
                          onChange={(e) => setOpinion(e.target.value)}
                          placeholder="可选"
                          value={opinion}
                        />
                      </label>
                    </>
                  ) : (
                    /* A/B 偏好模式 */
                    <div>
                      <p className="mb-3 text-sm font-medium">选择偏好：</p>
                      <div className="flex gap-3">
                        <button
                          className={`flex-1 rounded-lg border p-4 text-center transition-colors ${
                            abPreference === "a"
                              ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                              : "border-[var(--border)] hover:bg-[var(--surface-subtle)]"
                          }`}
                          onClick={() => setAbPreference("a")}
                          type="button"
                        >
                          <ThumbsUp className="mx-auto size-6 text-[var(--success)]" />
                          <p className="mt-2 text-sm font-medium">A 更好</p>
                        </button>
                        <button
                          className={`flex-1 rounded-lg border p-4 text-center transition-colors ${
                            abPreference === "equal"
                              ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                              : "border-[var(--border)] hover:bg-[var(--surface-subtle)]"
                          }`}
                          onClick={() => setAbPreference("equal")}
                          type="button"
                        >
                          <Equal className="mx-auto size-6 text-[var(--text-muted)]" />
                          <p className="mt-2 text-sm font-medium">相同</p>
                        </button>
                        <button
                          className={`flex-1 rounded-lg border p-4 text-center transition-colors ${
                            abPreference === "b"
                              ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                              : "border-[var(--border)] hover:bg-[var(--surface-subtle)]"
                          }`}
                          onClick={() => setAbPreference("b")}
                          type="button"
                        >
                          <ThumbsDown className="mx-auto size-6 text-[var(--danger)]" />
                          <p className="mt-2 text-sm font-medium">B 更好</p>
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="mt-4 flex gap-2">
                    <Button
                      disabled={acting}
                      loading={acting}
                      onClick={handleApprove}
                      variant="primary"
                    >
                      <CheckCircle2 className="mr-1.5 size-4" />
                      通过
                    </Button>
                    <Button
                      disabled={acting}
                      onClick={handleReject}
                      variant="ghost"
                    >
                      <XCircle className="mr-1.5 size-4" />
                      拒绝
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-[var(--text-muted)]">
                  该任务已审核完成。
                </p>
              )}
            </div>
          ) : (
            <div className="py-10 text-center text-sm text-[var(--text-muted)]">
              <ClipboardCheck className="mx-auto size-8" />
              <p className="mt-2">选择一个任务查看详情</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
