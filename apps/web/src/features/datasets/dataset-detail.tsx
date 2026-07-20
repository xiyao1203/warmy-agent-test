"use client";

import type {
  CreateTestCaseRequest,
  DatasetResponse,
  DatasetVersionResponse,
  ImportPreviewResponse,
  TestCaseResponse,
  TestCaseValidationResponse,
} from "@warmy/generated-api-client";
import {
  CheckCircle2,
  CheckSquare,
  Eye,
  Pencil,
  Plus,
  Square,
  Trash2,
} from "lucide-react";
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
  TableValue,
} from "@/components/ui/table";
import { Skeleton, Tooltip } from "@/components/uiverse";

import { ImportWizard } from "./import-wizard";
import { TestCaseDetail } from "./test-case-detail";
import { TestCaseEditor } from "./test-case-editor";
import { TestCaseTrialRun, type TrialRunTarget } from "./test-case-trial-run";

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
  onValidateCase?: (caseId: string) => Promise<TestCaseValidationResponse>;
  onMarkReady?: (caseId: string) => Promise<unknown>;
  onTrialRun?: (
    caseId: string,
    agentVersionId: string,
    environmentTemplateId: string,
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
  trialAgents?: TrialRunTarget[];
  trialEnvironments?: TrialRunTarget[];
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
  onValidateCase,
  onMarkReady,
  onTrialRun,
  projectId,
  trialAgents = [],
  trialEnvironments = [],
  versions = [],
}: DatasetDetailProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [viewingCase, setViewingCase] = useState<TestCaseResponse | null>(null);
  const [validationByCase, setValidationByCase] = useState<
    Record<string, TestCaseValidationResponse>
  >({});

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
      <div className="workspace-page">
        <Skeleton className="mb-2 h-4 w-24" />
        <Skeleton className="mb-1 h-8 w-48" />
        <Skeleton className="mb-6 h-4 w-64" />
        <Skeleton className="mb-4 h-10 w-full max-w-xs" />
        <Skeleton className="h-64 rounded-[var(--radius-lg)]" />
      </div>
    );
  }

  return (
    <div className="workspace-page">
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
            <Table className="w-full">
              <TableHeader className="bg-[var(--canvas-soft)]">
                <TableRow>
                  {canSelectCases && (
                    <TableHead className="w-px whitespace-nowrap">
                      <Tooltip
                        content={allSelected ? "取消全选" : "全选"}
                        side="bottom"
                      >
                        <Button
                          aria-label={allSelected ? "取消全选" : "全选"}
                          className="size-8 shrink-0 px-0"
                          onClick={toggleAll}
                          variant="ghost"
                        >
                          {allSelected ? (
                            <CheckSquare
                              aria-hidden="true"
                              className="size-4"
                            />
                          ) : (
                            <Square aria-hidden="true" className="size-4" />
                          )}
                        </Button>
                      </Tooltip>
                    </TableHead>
                  )}
                  <TableHead className="min-w-64">用例 / 目标</TableHead>
                  <TableHead className="whitespace-nowrap">
                    分类 / 状态
                  </TableHead>
                  <TableHead className="whitespace-nowrap">
                    优先级 / 风险
                  </TableHead>
                  <TableHead className="whitespace-nowrap">
                    自动化 / 模式
                  </TableHead>
                  <TableHead className="whitespace-nowrap">
                    步骤 / 断言
                  </TableHead>
                  <TableHead className="min-w-[26rem] whitespace-nowrap">
                    操作
                  </TableHead>
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
                        <Tooltip
                          content={selectedIds.has(c.id) ? "取消选中" : "选中"}
                          side="top"
                        >
                          <Button
                            aria-label={
                              selectedIds.has(c.id) ? "取消选中" : "选中"
                            }
                            className="size-8 shrink-0 px-0"
                            onClick={() => toggleSelect(c.id)}
                            variant="ghost"
                          >
                            {selectedIds.has(c.id) ? (
                              <CheckSquare
                                aria-hidden="true"
                                className="size-4 text-[var(--primary)]"
                              />
                            ) : (
                              <Square aria-hidden="true" className="size-4" />
                            )}
                          </Button>
                        </Tooltip>
                      </TableCell>
                    )}
                    <TableCell className="min-w-0">
                      <TableValue className="min-w-0">
                        <p className="truncate font-medium">{c.name}</p>
                        <p className="mt-0.5 truncate text-xs text-[var(--muted)]">
                          {c.case_key ?? "未编号"} · {c.component ?? "未分组件"}
                        </p>
                        <p className="mt-0.5 line-clamp-2 text-xs text-[var(--muted)]">
                          {c.objective || "未填写测试目标"}
                        </p>
                      </TableValue>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-center">
                      <div className="space-y-1">
                        <Badge>{caseTypeLabel(c.case_type)}</Badge>
                        <div>
                          <Badge
                            tone={
                              c.case_status === "ready" ? "accent" : "neutral"
                            }
                          >
                            {caseStatusLabel(c.case_status)}
                          </Badge>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-center">
                      <div className="space-y-1">
                        <Badge
                          tone={c.priority === "P0" ? "danger" : "neutral"}
                        >
                          {c.priority || "未设置"}
                        </Badge>
                        <div>
                          <Badge
                            tone={
                              c.risk_level === "high" ? "danger" : "neutral"
                            }
                          >
                            {riskLabel(c.risk_level)}
                          </Badge>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-center text-sm text-[var(--muted)]">
                      <p>{automationLabel(c.automation_status)}</p>
                      <p className="mt-1 text-xs">
                        {executionModeLabel(c.execution_mode)}
                      </p>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-center">
                      <p className="text-sm">{c.steps.length} 步</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        {c.assertions.length} 条断言
                      </p>
                    </TableCell>
                    <TableCell>
                      <div className="mx-auto flex w-fit max-w-full justify-center gap-1 whitespace-nowrap">
                        <Tooltip content="查看" side="top">
                          <Button
                            aria-label="查看详情"
                            className="h-8 w-8 shrink-0 px-0"
                            onClick={() => setViewingCase(c)}
                            variant="ghost"
                          >
                            <Eye aria-hidden="true" className="size-4" />
                          </Button>
                        </Tooltip>
                        {canEditExistingCases && onUpdateCase && (
                          <Tooltip content="编辑" side="top">
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
                          </Tooltip>
                        )}
                        {canEditExistingCases && onValidateCase && (
                          <Button
                            aria-label={`校验${c.name}`}
                            onClick={async () => {
                              const result = await onValidateCase(c.id);
                              setValidationByCase((current) => ({
                                ...current,
                                [c.id]: result,
                              }));
                            }}
                            variant="secondary"
                          >
                            校验
                          </Button>
                        )}
                        {canEditExistingCases &&
                          onMarkReady &&
                          c.case_status !== "ready" && (
                            <Button
                              aria-label={`标记${c.name}就绪`}
                              disabled={validationByCase[c.id]?.ready === false}
                              onClick={async () => {
                                await onMarkReady(c.id);
                                onRefresh?.();
                              }}
                              variant="secondary"
                            >
                              <CheckCircle2
                                aria-hidden="true"
                                className="mr-1 size-4"
                              />
                              就绪
                            </Button>
                          )}
                        {canEditExistingCases && onTrialRun && (
                          <TestCaseTrialRun
                            agents={trialAgents}
                            environments={trialEnvironments}
                            onRun={(agentVersionId, environmentTemplateId) =>
                              onTrialRun(
                                c.id,
                                agentVersionId,
                                environmentTemplateId,
                              )
                            }
                          />
                        )}
                        {canEditExistingCases && onDeleteCases && (
                          <Tooltip content="删除" side="top">
                            <Button
                              aria-label={`删除${c.name}`}
                              className="h-8 w-8 shrink-0 px-0"
                              onClick={() => void handleDeleteOne(c.id)}
                              variant="danger"
                            >
                              <Trash2 aria-hidden="true" className="size-4" />
                            </Button>
                          </Tooltip>
                        )}
                      </div>
                      {validationByCase[c.id] && (
                        <p
                          className={`mt-1 text-center text-xs ${validationByCase[c.id].ready ? "text-[var(--success)]" : "text-[var(--danger)]"}`}
                        >
                          {validationByCase[c.id].ready
                            ? "校验通过"
                            : `${validationByCase[c.id].issues.length} 个问题`}
                        </p>
                      )}
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

function caseTypeLabel(value: string) {
  return (
    (
      {
        functional: "功能",
        regression: "回归",
        smoke: "冒烟",
        integration: "集成",
        e2e: "端到端",
        security: "安全",
        performance: "性能",
        usability: "可用性",
        exploratory: "探索",
      } as Record<string, string>
    )[value] ?? value
  );
}

function caseStatusLabel(value: string) {
  return (
    (
      { draft: "草稿", ready: "就绪", deprecated: "已废弃" } as Record<
        string,
        string
      >
    )[value] ?? value
  );
}

function automationLabel(value: string) {
  return (
    (
      {
        manual: "人工",
        candidate: "自动化候选",
        automated: "已自动化",
      } as Record<string, string>
    )[value] ?? value
  );
}

function riskLabel(value: string | null) {
  if (!value) return "未设置";
  return (
    (
      { high: "高风险", medium: "中风险", low: "低风险" } as Record<
        string,
        string
      >
    )[value] ?? value
  );
}

function executionModeLabel(mode: string) {
  if (mode === "api") return "API";
  if (mode === "codex_explore") return "Codex 浏览器探索";
  return "浏览器";
}
