"use client";

import type {
  CreateTestCaseRequest,
  DatasetResponse,
  DatasetVersionResponse,
  ImportPreviewResponse,
  TestCaseResponse,
} from "@warmy/generated-api-client";
import { CheckSquare, Eye, Pencil, Plus, Square, Trash2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/uiverse";

import { ImportWizard } from "./import-wizard";
import { TestCaseDetail } from "./test-case-detail";
import { TestCaseEditor } from "./test-case-editor";

type DatasetDetailProps = {
  dataset: DatasetResponse;
  versions?: DatasetVersionResponse[];
  cases?: TestCaseResponse[];
  currentVersionId?: string;
  /** 当前版本是否为已发布（禁止导入） */
  currentVersionPublished?: boolean;
  loading?: boolean;
  onDeleteCases?: (caseIds: string[]) => Promise<unknown>;
  onCreateCase?: (payload: CreateTestCaseRequest) => Promise<unknown>;
  onUpdateCase?: (
    caseId: string,
    payload: CreateTestCaseRequest,
  ) => Promise<unknown>;
  onRefresh?: () => void;
  onImport?: (
    content: string,
    format: "json" | "jsonl" | "csv",
  ) => Promise<{ imported_count: number }>;
  onPreviewImport?: (
    content: string,
    format: "json" | "jsonl" | "csv",
  ) => Promise<ImportPreviewResponse>;
  projectId: string;
};

export function DatasetDetail({
  cases = [],
  currentVersionId,
  currentVersionPublished = false,
  dataset,
  loading = false,
  onCreateCase,
  onDeleteCases,
  onRefresh,
  onImport,
  onPreviewImport,
  onUpdateCase,
  projectId,
  versions = [],
}: DatasetDetailProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [viewingCase, setViewingCase] = useState<TestCaseResponse | null>(null);

  const filteredCases = useMemo(() => {
    if (!search.trim()) return cases;
    const q = search.toLowerCase();
    return cases.filter((c) => c.name.toLowerCase().includes(q));
  }, [cases, search]);

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleAll = useCallback(() => {
    setSelectedIds((prev) => {
      if (prev.size === filteredCases.length) return new Set();
      return new Set(filteredCases.map((c) => c.id));
    });
  }, [filteredCases]);

  const handleBatchDelete = useCallback(async () => {
    if (!onDeleteCases || currentVersionPublished || selectedIds.size === 0) {
      return;
    }
    setDeleting(true);
    try {
      await onDeleteCases(Array.from(selectedIds));
      setSelectedIds(new Set());
      onRefresh?.();
    } finally {
      setDeleting(false);
    }
  }, [currentVersionPublished, onDeleteCases, selectedIds, onRefresh]);

  const handleDeleteOne = useCallback(
    async (caseId: string) => {
      if (!onDeleteCases || currentVersionPublished) return;
      await onDeleteCases([caseId]);
      setSelectedIds((prev) => {
        const next = new Set(prev);
        next.delete(caseId);
        return next;
      });
      onRefresh?.();
    },
    [currentVersionPublished, onDeleteCases, onRefresh],
  );

  const canCreateCases = !currentVersionPublished && Boolean(onCreateCase);
  const canEditExistingCases =
    Boolean(currentVersionId) && !currentVersionPublished;
  const canSelectCases = canEditExistingCases && Boolean(onDeleteCases);
  const selectedCount = canSelectCases ? selectedIds.size : 0;
  const allSelected =
    filteredCases.length > 0 && selectedCount === filteredCases.length;

  const renderCreateCaseAction = useCallback(
    (label = "新增用例") => {
      if (!canCreateCases || !onCreateCase) return null;
      return (
        <TestCaseEditor
          onSubmit={async (payload) => {
            await onCreateCase(payload);
            onRefresh?.();
          }}
          triggerLabel={label}
          triggerIcon={<Plus aria-hidden="true" className="mr-1.5 size-4" />}
        />
      );
    },
    [canCreateCases, onCreateCase, onRefresh],
  );

  if (loading) {
    return (
      <div className="min-w-0 px-6 py-6">
        <Skeleton className="mb-2 h-4 w-24" />
        <Skeleton className="mb-1 h-8 w-48" />
        <Skeleton className="mb-6 h-4 w-64" />
        <Skeleton className="mb-4 h-10 w-full max-w-xs" />
        <Skeleton className="h-64 rounded-[var(--radius-lg)]" />
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <Link
        className="inline-flex items-center gap-1.5 text-sm text-[var(--muted)] hover:text-[var(--ink)]"
        href={`/projects/${projectId}/datasets`}
      >
        ← 返回用例集列表
      </Link>

      {/* ── 顶部 ──────────────────────────────────────────────────────── */}
      <header className="mt-4 flex flex-col gap-4 border-b border-[var(--hairline)] pb-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">
              {dataset.name}
            </h1>
            {currentVersionId && (
              <Badge tone="accent">v{currentVersionId.slice(0, 6)}</Badge>
            )}
          </div>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {dataset.description ||
              "这个用例集可以收纳手工新增、文件导入和测试 Agent 生成的用例。"}
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-start gap-2 lg:justify-end">
          {renderCreateCaseAction()}
          <ImportWizard
            disabled={currentVersionPublished}
            onImport={onImport}
            onPreview={onPreviewImport}
            onSuccess={onRefresh}
          />
          <Button asChild variant="secondary">
            <Link href={`/projects/${projectId}/test-plans`}>
              用这些用例创建测试计划
            </Link>
          </Button>
        </div>
      </header>

      {/* ── 版本信息 ───────────────────────────────────────────────────── */}
      {versions.length > 0 && (
        <section className="mt-4 flex gap-2 overflow-x-auto pb-2">
          {versions.map((v) => (
            <Badge
              key={v.id}
              tone={v.id === currentVersionId ? "accent" : "neutral"}
            >
              v{v.version_number} {v.status === "published" ? "已发布" : "草稿"}
            </Badge>
          ))}
        </section>
      )}

      <section className="mt-4 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--canvas-soft)] px-4 py-3">
        <div className="flex flex-col gap-2 text-sm lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="font-medium text-[var(--ink)]">
              {currentVersionPublished
                ? "当前版本已发布，只读"
                : "当前版本为草稿，可维护测试用例"}
            </p>
            <p className="mt-1 text-xs text-[var(--muted)]">
              新增、编辑、删除和导入都写入当前用例集草稿；发布后版本会固化，测试计划选择已发布版本执行。
            </p>
          </div>
          <Badge tone={currentVersionPublished ? "accent" : "neutral"}>
            {currentVersionPublished
              ? "可被测试计划引用"
              : "发布后用于测试计划"}
          </Badge>
        </div>
      </section>

      {/* ── 用例列表 ───────────────────────────────────────────────────── */}
      <section className="mt-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Input
              className="w-64"
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索用例…"
              value={search}
            />
            {selectedCount > 0 && (
              <span className="text-xs text-[var(--muted)]">
                已选 {selectedCount} 项
              </span>
            )}
          </div>
          {selectedCount > 0 && canSelectCases && (
            <Button
              disabled={deleting}
              loading={deleting}
              onClick={handleBatchDelete}
              variant="danger"
            >
              <Trash2 aria-hidden="true" className="mr-1 size-4" />
              删除选中 ({selectedCount})
            </Button>
          )}
        </div>

        {!filteredCases.length ? (
          <EmptyState
            action={search ? undefined : renderCreateCaseAction()}
            description={
              search ? "没有匹配的用例。" : "暂无用例，可以新增或导入。"
            }
            title={search ? "无匹配结果" : "暂无测试用例"}
          />
        ) : (
          <div className="mt-3 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
            <Table className="w-full table-fixed">
              <TableHeader className="bg-[var(--canvas-soft)]">
                <TableRow>
                  {canSelectCases && (
                    <TableHead className="w-[4%]">
                      <button
                        aria-label={allSelected ? "取消全选" : "全选"}
                        onClick={toggleAll}
                        type="button"
                      >
                        {allSelected ? (
                          <CheckSquare className="size-4" />
                        ) : (
                          <Square className="size-4" />
                        )}
                      </button>
                    </TableHead>
                  )}
                  <TableHead className={canSelectCases ? "w-[34%]" : "w-[38%]"}>
                    用例名称
                  </TableHead>
                  <TableHead className="w-[11%]">优先级</TableHead>
                  <TableHead className="w-[12%]">风险等级</TableHead>
                  <TableHead className="w-[13%]">执行模式</TableHead>
                  <TableHead className="w-[12%]">断言</TableHead>
                  <TableHead className="w-[18%]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCases.map((c) => (
                  <TableRow
                    className="transition-colors hover:bg-[var(--canvas-soft)]"
                    key={c.id}
                  >
                    {canSelectCases && (
                      <TableCell>
                        <button
                          aria-label={
                            selectedIds.has(c.id) ? "取消选中" : "选中"
                          }
                          onClick={() => toggleSelect(c.id)}
                          type="button"
                        >
                          {selectedIds.has(c.id) ? (
                            <CheckSquare className="size-4 text-[var(--primary)]" />
                          ) : (
                            <Square className="size-4" />
                          )}
                        </button>
                      </TableCell>
                    )}
                    <TableCell className="min-w-0">
                      <div className="mx-auto min-w-0 max-w-full text-left">
                        <p className="truncate font-medium">{c.name}</p>
                        <p className="mt-0.5 truncate text-xs text-[var(--muted)]">
                          {c.input
                            ? JSON.stringify(c.input).slice(0, 80)
                            : "无输入"}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-center">
                      <Badge tone={c.priority === "P0" ? "danger" : "neutral"}>
                        {c.priority || "P2"}
                      </Badge>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-center">
                      <Badge
                        tone={c.risk_level === "high" ? "danger" : "neutral"}
                      >
                        {c.risk_level || "中"}
                      </Badge>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-center text-sm text-[var(--muted)]">
                      {executionModeLabel(c.execution_mode)}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-center">
                      <Badge tone={c.assertions?.length ? "accent" : "neutral"}>
                        {c.assertions?.length
                          ? `${c.assertions.length} 条`
                          : "未配置"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="mx-auto flex w-fit max-w-full justify-center gap-1 whitespace-nowrap">
                        <Button
                          aria-label="查看详情"
                          className="h-8 w-8 shrink-0 px-0"
                          onClick={() => setViewingCase(c)}
                          variant="ghost"
                        >
                          <Eye className="size-4" />
                        </Button>
                        {canEditExistingCases && onUpdateCase && (
                          <TestCaseEditor
                            caseItem={c}
                            onSubmit={async (payload) => {
                              await onUpdateCase(c.id, payload);
                              onRefresh?.();
                            }}
                            triggerAriaLabel={`编辑${c.name}`}
                            triggerIcon={
                              <Pencil aria-hidden="true" className="size-4" />
                            }
                            triggerLabel="编辑"
                          />
                        )}
                        {canEditExistingCases && onDeleteCases && (
                          <Button
                            aria-label={`删除${c.name}`}
                            className="h-8 w-8 shrink-0 px-0"
                            onClick={() => void handleDeleteOne(c.id)}
                            variant="danger"
                          >
                            <Trash2 aria-hidden="true" className="size-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      {/* ── 详情抽屉 ────────────────────────────────────────────────────── */}
      {viewingCase && (
        <TestCaseDetail
          caseItem={viewingCase}
          open={true}
          onClose={() => setViewingCase(null)}
        />
      )}
    </div>
  );
}

function executionModeLabel(mode: string) {
  if (mode === "api") return "API";
  if (mode === "codex_explore") return "Codex 浏览器探索";
  return "浏览器";
}
