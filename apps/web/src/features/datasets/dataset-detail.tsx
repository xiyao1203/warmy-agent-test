"use client";

import type {
  CreateTestCaseRequest,
  DatasetResponse,
  DatasetVersionResponse,
  TestCaseResponse,
} from "@warmy/generated-api-client";
import { CheckSquare, Eye, Square, Trash2 } from "lucide-react";
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

type DatasetDetailProps = {
  dataset: DatasetResponse;
  versions?: DatasetVersionResponse[];
  cases?: TestCaseResponse[];
  currentVersionId?: string;
  loading?: boolean;
  onDeleteCases?: (caseIds: string[]) => Promise<unknown>;
  onCreateCase?: (payload: CreateTestCaseRequest) => Promise<unknown>;
  onRefresh?: () => void;
  projectId: string;
};

export function DatasetDetail({
  cases = [],
  currentVersionId,
  dataset,
  loading = false,
  onDeleteCases,
  onRefresh,
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
    if (!onDeleteCases || selectedIds.size === 0) return;
    setDeleting(true);
    try {
      await onDeleteCases(Array.from(selectedIds));
      setSelectedIds(new Set());
      onRefresh?.();
    } finally {
      setDeleting(false);
    }
  }, [onDeleteCases, selectedIds, onRefresh]);

  const selectedCount = selectedIds.size;
  const allSelected =
    filteredCases.length > 0 && selectedCount === filteredCases.length;

  if (loading) {
    return (
      <div className="min-w-0 px-6 py-6">
        <Skeleton className="mb-2 h-4 w-24" />
        <Skeleton className="mb-1 h-8 w-48" />
        <Skeleton className="mb-6 h-4 w-64" />
        <Skeleton className="mb-4 h-10 w-full max-w-xs" />
        <Skeleton className="h-64 rounded-[var(--radius-md)]" />
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <Link
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
        href={`/projects/${projectId}/datasets`}
      >
        ← 返回数据集列表
      </Link>

      {/* ── 顶部 ──────────────────────────────────────────────────────── */}
      <header className="mt-4 flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">
              {dataset.name}
            </h1>
            {currentVersionId && (
              <Badge tone="accent">v{currentVersionId.slice(0, 6)}</Badge>
            )}
          </div>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {dataset.description || "暂无描述"}
          </p>
        </div>
        <ImportWizard onSuccess={onRefresh} />
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
              <span className="text-xs text-[var(--text-muted)]">
                已选 {selectedCount} 项
              </span>
            )}
          </div>
          {selectedCount > 0 && onDeleteCases && (
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
            description={
              search ? "没有匹配的用例。" : "暂无用例，点击右上角导入或创建。"
            }
            title={search ? "无匹配结果" : "暂无测试用例"}
          />
        ) : (
          <div className="mt-3 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
            <Table>
              <TableHeader className="bg-[var(--surface-subtle)]">
                <TableRow>
                  <TableHead className="w-10">
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
                  <TableHead>用例名称</TableHead>
                  <TableHead className="w-32 text-center">优先级</TableHead>
                  <TableHead className="w-32 text-center">风险等级</TableHead>
                  <TableHead className="w-40 text-center">执行模式</TableHead>
                  <TableHead className="w-20 text-center">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCases.map((c) => (
                  <TableRow
                    className="transition-colors hover:bg-[var(--surface-subtle)]"
                    key={c.id}
                  >
                    <TableCell>
                      <button
                        aria-label={selectedIds.has(c.id) ? "取消选中" : "选中"}
                        onClick={() => toggleSelect(c.id)}
                        type="button"
                      >
                        {selectedIds.has(c.id) ? (
                          <CheckSquare className="size-4 text-[var(--accent)]" />
                        ) : (
                          <Square className="size-4" />
                        )}
                      </button>
                    </TableCell>
                    <TableCell>
                      <p className="truncate font-medium">{c.name}</p>
                      <p className="mt-0.5 truncate text-xs text-[var(--text-muted)]">
                        {c.input
                          ? JSON.stringify(c.input).slice(0, 80)
                          : "无输入"}
                      </p>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge tone={c.priority === "P0" ? "danger" : "neutral"}>
                        {c.priority || "P2"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge
                        tone={c.risk_level === "high" ? "danger" : "neutral"}
                      >
                        {c.risk_level || "中"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center text-sm text-[var(--text-muted)]">
                      {c.execution_mode === "api" ? "API" : "浏览器"}
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex justify-center gap-1">
                        <Button
                          aria-label="查看详情"
                          onClick={() => setViewingCase(c)}
                          variant="ghost"
                        >
                          <Eye className="size-4" />
                        </Button>
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
