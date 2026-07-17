"use client";

import {
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Equal,
  PlayCircle,
  ShieldAlert,
  SkipForward,
  ThumbsDown,
  ThumbsUp,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ResourceReferenceLink } from "@/components/ui/resource-reference-link";

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

const STATUS_LABELS: Record<string, string> = {
  approved: "已通过",
  pending: "待处理",
  rejected: "已拒绝",
  skipped: "暂不处理",
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
      <div className="grid min-h-[40vh] place-items-center text-sm text-[var(--muted)]">
        正在加载审核任务…
      </div>
    );
  }

  const pendingCount = tasks.filter((t) => t.status === "pending").length;

  return (
    <div className="workspace-page">
      <header className="flex items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">人工审核</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {pendingCount > 0
              ? `${pendingCount} 个待处理任务`
              : "暂无待处理任务"}
            ，低置信、高风险或评分冲突的运行结果会自动进入这里。
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
                    ? "待处理"
                    : s === "approved"
                      ? "已通过"
                      : s === "rejected"
                        ? "已拒绝"
                        : "暂不处理"}
              </Button>
            ),
          )}
        </div>
      </header>

      <section className="mt-5 grid gap-3 md:grid-cols-4">
        <FlowCard
          description="低置信、高风险自动收集"
          href={`/projects/${projectId}/runs`}
          icon={<PlayCircle aria-hidden="true" className="size-4" />}
          label="1. 运行产生任务"
        />
        <FlowCard
          description="查看证据后给出结论"
          icon={<ClipboardCheck aria-hidden="true" className="size-4" />}
          label="2. 人工审核"
        />
        <FlowCard
          description="结合安全发现判断风险"
          href={`/projects/${projectId}/security`}
          icon={<ShieldAlert aria-hidden="true" className="size-4" />}
          label="3. 查看安全测试"
        />
        <FlowCard
          description="未处理任务会影响放行"
          href={`/projects/${projectId}/gates`}
          icon={<CheckCircle2 aria-hidden="true" className="size-4" />}
          label="4. 发布门禁放行"
        />
      </section>

      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_24rem] gap-5 max-[1100px]:grid-cols-1">
        {/* 任务列表 */}
        <ul className="space-y-2">
          {tasks.length === 0 ? (
            <li className="rounded border border-dashed border-[var(--hairline)] p-8 text-center text-sm text-[var(--muted)]">
              <ClipboardCheck className="mx-auto size-8" />
              <p className="mt-2 font-medium text-[var(--ink)]">暂无审核任务</p>
              <p className="mx-auto mt-1 max-w-md">
                运行完成后，需要人工判断的用例会自动出现在这里；处理完后，发布门禁会用待处理数量做放行判断。
              </p>
              <div className="mt-4 flex justify-center gap-3">
                <Link
                  className="text-sm font-medium text-[var(--primary)] hover:underline"
                  href={`/projects/${projectId}/runs`}
                >
                  去运行中心
                </Link>
                <Link
                  className="text-sm font-medium text-[var(--primary)] hover:underline"
                  href={`/projects/${projectId}/gates`}
                >
                  查看发布门禁
                </Link>
              </div>
            </li>
          ) : (
            tasks.map((t) => (
              <li key={t.id}>
                <button
                  className={`flex w-full items-center gap-3 rounded border px-4 py-3 text-left text-sm transition-colors ${
                    selected?.id === t.id
                      ? "border-[var(--primary)] bg-[var(--primary-subtle)]"
                      : "border-[var(--hairline)] hover:bg-[var(--canvas-soft)]"
                  }`}
                  onClick={() => setSelected(t)}
                  type="button"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-mono text-xs">
                      {t.run_case_id.slice(0, 12)}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      置信度 {(t.confidence * 100).toFixed(0)}%
                      {t.score != null ? ` · 评分 ${t.score.toFixed(2)}` : ""}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      运行 {t.run_ref?.name ?? "暂无数据"} · 用例{" "}
                      {t.case_ref?.name ?? t.run_case_id.slice(0, 12)}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      原因 {t.enqueue_reason || "low_confidence"} · 优先级{" "}
                      {t.priority ?? 0} · 等待 {formatAge(t.age_seconds ?? 0)} ·
                      处理人 {t.assignee_ref?.name ?? "未分配"}
                    </p>
                  </div>
                  <Badge tone={STATUS_TONES[t.status] ?? "neutral"}>
                    {STATUS_LABELS[t.status] ?? t.status}
                  </Badge>
                  {t.status === "pending" ? (
                    <Button
                      aria-label={`暂不处理 ${t.run_case_id.slice(0, 12)}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        void handleSkip(t.id);
                      }}
                      variant="ghost"
                    >
                      <SkipForward className="mr-1 size-4" />
                      暂不处理
                    </Button>
                  ) : null}
                  <ChevronRight className="size-4 text-[var(--muted)]" />
                </button>
              </li>
            ))
          )}
        </ul>

        {/* 详情 + 评分面板 */}
        <aside className="h-fit rounded border border-[var(--hairline)] bg-[var(--surface)] p-5">
          {selected ? (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-medium text-[var(--muted)]">
                  用例 ID
                </p>
                <p className="mt-1 font-mono text-sm">{selected.run_case_id}</p>
              </div>
              <div className="grid gap-2 text-xs text-[var(--muted)]">
                <p>
                  运行：
                  <ResourceReferenceLink reference={selected.run_ref} />
                </p>
                <p>
                  用例：
                  <ResourceReferenceLink reference={selected.case_ref} />
                </p>
                <p>
                  处理人：
                  <ResourceReferenceLink
                    emptyLabel="未分配"
                    reference={selected.assignee_ref}
                  />
                </p>
                <p>
                  进入原因 {selected.enqueue_reason || "low_confidence"} ·
                  优先级 {selected.priority ?? 0} · 等待{" "}
                  {formatAge(selected.age_seconds ?? 0)}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-[var(--muted)]">置信度</p>
                  <p className="font-semibold">
                    {(selected.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[var(--muted)]">状态</p>
                  <Badge tone={STATUS_TONES[selected.status] ?? "neutral"}>
                    {STATUS_LABELS[selected.status] ?? selected.status}
                  </Badge>
                </div>
                {selected.score != null ? (
                  <div>
                    <p className="text-xs text-[var(--muted)]">评分</p>
                    <p className="font-semibold">{selected.score.toFixed(2)}</p>
                  </div>
                ) : null}
                {selected.opinion ? (
                  <div className="col-span-2">
                    <p className="text-xs text-[var(--muted)]">审核意见</p>
                    <p className="mt-1 text-sm">{selected.opinion}</p>
                  </div>
                ) : null}
              </div>

              <div className="rounded border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3 text-xs leading-5 text-[var(--muted)]">
                这条任务来自测试执行结果。先回到运行中心核对输入、输出、Trace
                和评分证据，再给出通过或拒绝结论。
                <div className="mt-2 flex flex-wrap gap-3">
                  <Link
                    className="font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/runs`}
                  >
                    查看运行证据
                  </Link>
                  <Link
                    className="font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/gates`}
                  >
                    查看门禁影响
                  </Link>
                </div>
              </div>

              {selected.status === "pending" ? (
                <div className="border-t border-[var(--hairline)] pt-4">
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
                              ? "border-[var(--primary)] bg-[var(--primary-subtle)]"
                              : "border-[var(--hairline)] hover:bg-[var(--canvas-soft)]"
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
                              ? "border-[var(--primary)] bg-[var(--primary-subtle)]"
                              : "border-[var(--hairline)] hover:bg-[var(--canvas-soft)]"
                          }`}
                          onClick={() => setAbPreference("equal")}
                          type="button"
                        >
                          <Equal className="mx-auto size-6 text-[var(--muted)]" />
                          <p className="mt-2 text-sm font-medium">相同</p>
                        </button>
                        <button
                          className={`flex-1 rounded-lg border p-4 text-center transition-colors ${
                            abPreference === "b"
                              ? "border-[var(--primary)] bg-[var(--primary-subtle)]"
                              : "border-[var(--hairline)] hover:bg-[var(--canvas-soft)]"
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
                <p className="text-xs text-[var(--muted)]">
                  该任务已审核完成。
                </p>
              )}
            </div>
          ) : (
            <div className="py-10 text-center text-sm text-[var(--muted)]">
              <ClipboardCheck className="mx-auto size-8" />
              <p className="mt-2">选择一个任务查看详情</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function formatAge(seconds: number) {
  if (seconds < 60) return `${seconds} 秒`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时`;
  return `${Math.floor(seconds / 86400)} 天`;
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
