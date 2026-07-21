"use client";

import {
  Archive,
  Edit3,
  FolderKanban,
  PlayCircle,
  Plus,
  Search,
} from "lucide-react";
import { useMemo, useState } from "react";
import type {
  CreateProjectRequest,
  ProjectResponse,
  RenameProjectRequest,
} from "@warmy/generated-api-client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { ListToolbar } from "@/components/ui/list-toolbar";
import { ResourcePagination } from "@/components/ui/resource-pagination";
import { ResourceReferenceLink } from "@/components/ui/resource-reference-link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableValue,
} from "@/components/ui/table";
import {
  TableActions,
  TableActionButton,
  tableActionCellClass,
  tableActionHeadClass,
} from "@/components/ui/table-actions";
import { TruncatedText } from "@/components/ui/truncated-text";
import {
  ProjectEmptyVisual,
  ProjectLoadingMotion,
} from "@/components/visuals/project-state-visuals";
import type { PageSize } from "@/lib/pagination";

type ProjectListScreenProps = {
  error?: "service";
  loading?: boolean;
  onArchive: (projectId: string) => Promise<unknown>;
  onCreate: (payload: CreateProjectRequest) => Promise<unknown>;
  onOpen: (projectId: string) => void;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: PageSize) => void;
  onRename: (
    projectId: string,
    payload: RenameProjectRequest,
  ) => Promise<unknown>;
  page?: number;
  pageSize?: PageSize;
  projects: ProjectResponse[];
  total?: number;
  totalPages?: number;
};

type ProjectStatusFilter = "active" | "all" | "archived";

export function ProjectListScreen({
  error,
  loading = false,
  onArchive,
  onCreate,
  onOpen,
  onPageChange = () => undefined,
  onPageSizeChange = () => undefined,
  onRename,
  page = 1,
  pageSize = 10,
  projects,
  total = projects.length,
  totalPages = projects.length > 0 ? 1 : 0,
}: ProjectListScreenProps) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ProjectStatusFilter>("all");
  const [editingProject, setEditingProject] = useState<ProjectResponse | null>(
    null,
  );
  const [editingName, setEditingName] = useState("");
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [formError, setFormError] = useState("");

  const activeCount = useMemo(
    () => projects.filter((project) => !project.archived).length,
    [projects],
  );
  const filteredProjects = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return projects.filter((project) => {
      const matchesKeyword =
        !keyword ||
        project.name.toLowerCase().includes(keyword) ||
        project.id.toLowerCase().includes(keyword);
      const matchesStatus =
        status === "all" ||
        (status === "active" && !project.archived) ||
        (status === "archived" && project.archived);
      return matchesKeyword && matchesStatus;
    });
  }, [projects, query, status]);

  function startRename(project: ProjectResponse) {
    setEditingProject(project);
    setEditingName(project.name);
    setFormError("");
  }

  async function submitRename(project: ProjectResponse) {
    const name = editingName.trim();
    if (!name || pendingAction) return;

    setPendingAction(`rename:${project.id}`);
    setFormError("");
    try {
      await onRename(project.id, { name });
      setEditingProject(null);
      setEditingName("");
    } catch {
      setFormError("保存项目名称失败，请重试。");
    } finally {
      setPendingAction(null);
    }
  }

  async function submitArchive(project: ProjectResponse) {
    if (project.archived || pendingAction) return;

    setPendingAction(`archive:${project.id}`);
    setFormError("");
    try {
      await onArchive(project.id);
    } catch {
      setFormError("归档项目失败，请重试。");
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <div className="workspace-page">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="font-display text-page-title" data-font-role="display">
            项目管理
          </h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            管理测试资产所在项目，进入项目后默认打开测试 Agent。
          </p>
        </div>
        <CreateProjectDialog onCreate={onCreate} />
      </header>

      <section className="grid grid-cols-3 border-b border-[var(--hairline)] py-4 text-sm max-[760px]:grid-cols-1 max-[760px]:gap-4">
        <Summary id="total" label="全部项目" value={total} />
        <Summary id="active" label="当前页运行中" value={activeCount} />
        <Summary
          id="archived"
          label="当前页已归档"
          value={projects.length - activeCount}
        />
      </section>

      <ListToolbar className="border-t-0" data-testid="project-filter-bar">
        <label className="relative min-w-0 flex-1 max-[760px]:w-full">
          <span className="sr-only">搜索项目</span>
          <Search
            aria-hidden="true"
            className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]"
          />
          <Input
            className="pl-9"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索项目名称或 ID"
            value={query}
          />
        </label>
        <DropdownSelect
          aria-label="按项目状态筛选"
          className="h-9 basis-40 shrink-0 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 text-sm max-[760px]:basis-auto"
          onChange={(event) =>
            setStatus(event.target.value as ProjectStatusFilter)
          }
          value={status}
        >
          <option value="all">全部状态</option>
          <option value="active">运行中</option>
          <option value="archived">已归档</option>
        </DropdownSelect>
      </ListToolbar>

      {formError ? (
        <p className="mb-3 text-sm text-[var(--danger)]" role="alert">
          {formError}
        </p>
      ) : null}

      <ProjectListState
        error={error}
        loading={loading}
        onCreate={onCreate}
        projectCount={projects.length}
      />

      {!loading && !error && projects.length > 0 ? (
        <section className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
          {filteredProjects.length === 0 ? (
            <EmptyState
              description="尝试修改关键词或状态筛选。"
              title="没有匹配的项目"
            />
          ) : (
            <Table className="w-full max-[640px]:block">
              <TableHeader className="bg-[var(--canvas-soft)] max-[640px]:hidden">
                <TableRow>
                  <TableHead className="min-w-60">项目</TableHead>
                  <TableHead className="whitespace-nowrap">状态</TableHead>
                  <TableHead className="min-w-52">资产概览</TableHead>
                  <TableHead className="min-w-44 whitespace-nowrap">
                    最近运行
                  </TableHead>
                  <TableHead className={tableActionHeadClass}>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="max-[640px]:block">
                {filteredProjects.map((project) => {
                  const archivePending =
                    pendingAction === `archive:${project.id}`;

                  return (
                    <TableRow
                      className="transition-colors hover:bg-[var(--canvas-soft)] max-[640px]:grid max-[640px]:grid-cols-[5rem_minmax(0,1fr)] max-[640px]:gap-x-3 max-[640px]:gap-y-2 max-[640px]:p-4"
                      key={project.id}
                    >
                      <TableCell className="max-[640px]:col-span-2 max-[640px]:block max-[640px]:h-auto max-[640px]:p-0 max-[640px]:pb-1">
                        <div className="mx-auto flex w-full max-w-80 min-w-0 items-center gap-3 text-left max-[640px]:mx-0 max-[640px]:max-w-full">
                          <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--canvas-soft)] text-[var(--primary)]">
                            <FolderKanban
                              aria-hidden="true"
                              className="size-4"
                            />
                          </span>
                          <div className="min-w-0">
                            <div className="flex min-w-0 items-center gap-1.5">
                              <span className="shrink-0 font-mono text-xs text-[var(--muted)]">
                                {project.key}
                              </span>
                              <TruncatedText className="font-medium">
                                {project.name}
                              </TruncatedText>
                            </div>
                            <TruncatedText className="mt-0.5 text-xs text-[var(--muted)]">
                              {project.description || project.id}
                            </TruncatedText>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="max-[640px]:contents">
                        <span className="hidden self-center text-left text-sm text-[var(--muted)] max-[640px]:block">
                          状态
                        </span>
                        <span className="text-center max-[640px]:text-left">
                          <Badge
                            tone={project.archived ? "neutral" : "success"}
                          >
                            {project.archived ? "已归档" : "运行中"}
                          </Badge>
                        </span>
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-[var(--muted)] max-[640px]:contents">
                        <span className="hidden self-center text-left max-[640px]:block">
                          资产概览
                        </span>
                        <TableValue>
                          <p>
                            成员 {project.member_count ?? 0} · Agent{" "}
                            {project.agent_count ?? 0} · 用例集{" "}
                            {project.dataset_count ?? 0}
                          </p>
                          <p>
                            用例 {project.test_case_count ?? 0} · 计划{" "}
                            {project.test_plan_count ?? 0} · 环境{" "}
                            {project.active_environment_count ?? 0}
                          </p>
                          <p>待审核 {project.open_review_count ?? 0}</p>
                        </TableValue>
                      </TableCell>
                      <TableCell className="text-left text-xs max-[640px]:contents">
                        <span className="hidden self-center text-left text-[var(--muted)] max-[640px]:block">
                          最近运行
                        </span>
                        <TableValue className="space-y-1">
                          <ResourceReferenceLink reference={project.last_run} />
                          <p className="text-[var(--muted)]">
                            {project.last_run_at
                              ? new Date(project.last_run_at).toLocaleString(
                                  "zh-CN",
                                )
                              : "尚未执行"}
                          </p>
                        </TableValue>
                      </TableCell>
                      <TableCell
                        className={`${tableActionCellClass} max-[640px]:contents`}
                      >
                        <span className="hidden self-center text-left text-sm text-[var(--muted)] max-[640px]:block">
                          操作
                        </span>
                        <TableActions label={project.name}>
                          <TableActionButton
                            accessibleLabel={`进入${project.name} 测试 Agent`}
                            disabled={project.archived}
                            label="进入"
                            onClick={() => onOpen(project.id)}
                          >
                            <PlayCircle aria-hidden="true" />
                          </TableActionButton>
                          <TableActionButton
                            accessibleLabel={`编辑${project.name}`}
                            disabled={project.archived}
                            label="编辑"
                            onClick={() => startRename(project)}
                          >
                            <Edit3 aria-hidden="true" />
                          </TableActionButton>
                          <TableActionButton
                            accessibleLabel={`归档${project.name}`}
                            disabled={project.archived || archivePending}
                            label="归档"
                            onClick={() => submitArchive(project)}
                            tone="danger"
                          >
                            <Archive aria-hidden="true" />
                          </TableActionButton>
                        </TableActions>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
          <ResourcePagination
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
            page={page}
            pageSize={pageSize}
            total={total}
            totalPages={totalPages}
          />
        </section>
      ) : null}
      <Dialog
        onOpenChange={(open) => {
          if (!open && !pendingAction) {
            setEditingProject(null);
            setEditingName("");
            setFormError("");
          }
        }}
        open={Boolean(editingProject)}
      >
        <DialogContent>
          <DialogTitle>编辑项目</DialogTitle>
          <DialogDescription>
            修改项目名称，不会影响项目 ID 和已有测试资产。
          </DialogDescription>
          <div className="mt-5 space-y-4">
            <label className="block text-sm font-medium">
              项目名称
              <Input
                autoFocus
                className="mt-1.5"
                onChange={(event) => {
                  setEditingName(event.target.value);
                  if (formError) setFormError("");
                }}
                value={editingName}
              />
            </label>
            {formError ? (
              <p className="text-sm text-[var(--danger)]" role="alert">
                {formError}
              </p>
            ) : null}
            <div className="flex justify-end gap-2">
              <Button
                disabled={Boolean(pendingAction)}
                onClick={() => setEditingProject(null)}
                type="button"
              >
                取消
              </Button>
              <Button
                disabled={!editingName.trim() || Boolean(pendingAction)}
                loading={Boolean(
                  editingProject &&
                  pendingAction === `rename:${editingProject.id}`,
                )}
                onClick={() => editingProject && submitRename(editingProject)}
                type="button"
                variant="primary"
              >
                保存修改
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function CreateProjectDialog({
  onCreate,
}: {
  onCreate: (payload: CreateProjectRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("请输入项目名称");
      return;
    }

    setSubmitting(true);
    try {
      await onCreate({ name: trimmedName });
      setOpen(false);
      setName("");
      setError("");
    } catch {
      setError("创建项目失败，请重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          新建项目
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>新建项目</DialogTitle>
        <DialogDescription>
          项目是测试资产、运行记录和权限隔离的基本单元。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            项目名称
            <Input
              className="mt-1.5"
              onChange={(event) => {
                setName(event.target.value);
                if (error) setError("");
              }}
              placeholder="例如：客服 Agent 回归测试"
              value={name}
            />
          </label>
          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button
              disabled={submitting}
              onClick={() => setOpen(false)}
              type="button"
            >
              取消
            </Button>
            <Button
              disabled={submitting}
              loading={submitting}
              onClick={submit}
              type="button"
              variant="primary"
            >
              保存项目
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Summary({
  id,
  label,
  value,
}: {
  id: "active" | "archived" | "total";
  label: string;
  value: number;
}) {
  return (
    <div>
      <div
        className="font-display text-lg font-semibold"
        data-font-role="display-number"
        data-testid={`project-summary-${id}`}
      >
        {value}
      </div>
      <div className="mt-0.5 text-xs text-[var(--muted)]">{label}</div>
    </div>
  );
}

function ProjectListState({
  error,
  loading,
  onCreate,
  projectCount,
}: {
  error?: "service";
  loading: boolean;
  onCreate: (payload: CreateProjectRequest) => Promise<unknown>;
  projectCount: number;
}) {
  if (loading) {
    return <ProjectLoadingMotion />;
  }

  if (error) {
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--danger)] bg-[var(--danger-subtle)] px-4 py-3 text-sm text-[var(--danger)]">
        项目列表暂时不可用，请刷新后重试。
      </div>
    );
  }

  if (projectCount === 0) {
    return (
      <section className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        <EmptyState
          action={<CreateProjectDialog onCreate={onCreate} />}
          description="创建第一个项目后即可进入测试 Agent。"
          title="暂无项目"
          visual={<ProjectEmptyVisual />}
        />
      </section>
    );
  }

  return null;
}
