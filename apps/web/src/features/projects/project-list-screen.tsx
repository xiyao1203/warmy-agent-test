"use client";

import {
  Archive,
  Edit3,
  FolderKanban,
  PlayCircle,
  Plus,
  Save,
  X,
} from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";
import type {
  CreateProjectRequest,
  ProjectResponse,
  RenameProjectRequest,
} from "@warmy/generated-api-client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type ProjectListScreenProps = {
  error?: "service";
  loading?: boolean;
  onArchive: (projectId: string) => Promise<unknown>;
  onCreate: (payload: CreateProjectRequest) => Promise<unknown>;
  onOpen: (projectId: string) => void;
  onRename: (
    projectId: string,
    payload: RenameProjectRequest,
  ) => Promise<unknown>;
  projects: ProjectResponse[];
};

export function ProjectListScreen({
  error,
  loading = false,
  onArchive,
  onCreate,
  onOpen,
  onRename,
  projects,
}: ProjectListScreenProps) {
  const [newName, setNewName] = useState("");
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [formError, setFormError] = useState("");

  const activeCount = useMemo(
    () => projects.filter((project) => !project.archived).length,
    [projects],
  );

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = newName.trim();
    if (!name || pendingAction) return;

    setPendingAction("create");
    setFormError("");
    try {
      await onCreate({ name });
      setNewName("");
    } catch {
      setFormError("创建项目失败，请重试。");
    } finally {
      setPendingAction(null);
    }
  }

  function startRename(project: ProjectResponse) {
    setEditingProjectId(project.id);
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
      setEditingProjectId(null);
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
    <section className="min-h-[calc(100vh-3.5rem)] bg-[var(--canvas)] text-[var(--ink)]">
      <div className="border-b border-[var(--hairline)] px-5 py-5 sm:px-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium text-[var(--primary)]">
              项目工作台
            </p>
            <h1 className="mt-2 text-[32px] font-semibold leading-tight tracking-normal">
              项目管理
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--body)]">
              集中管理测试资产所在项目，进入项目后默认打开测试 Agent。
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <Metric label="全部项目" value={projects.length} />
            <Metric label="可用项目" value={activeCount} />
            <Metric label="归档项目" value={projects.length - activeCount} />
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-5 py-6 sm:px-8">
        <form
          className="flex flex-col gap-3 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] p-4 sm:flex-row sm:items-end"
          onSubmit={handleCreate}
        >
          <label className="min-w-0 flex-1 text-sm font-medium">
            新建项目名称
            <Input
              className="mt-1.5 h-10"
              onChange={(event) => {
                setNewName(event.target.value);
                if (formError) setFormError("");
              }}
              placeholder="例如：客服 Agent 回归测试"
              value={newName}
            />
          </label>
          <Button
            className="h-10 shrink-0"
            disabled={!newName.trim() || pendingAction === "create"}
            loading={pendingAction === "create"}
            type="submit"
            variant="primary"
          >
            <Plus aria-hidden="true" className="size-4" />
            新建项目
          </Button>
        </form>

        {formError ? (
          <p className="mt-3 text-sm text-[var(--danger)]" role="alert">
            {formError}
          </p>
        ) : null}

        <ProjectListState
          error={error}
          loading={loading}
          projectCount={projects.length}
        />

        {projects.length > 0 ? (
          <div className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)]">
            <div className="hidden grid-cols-[minmax(0,1.5fr)_8rem_15rem] gap-4 border-b border-[var(--hairline)] px-4 py-3 text-xs font-medium text-[var(--muted)] md:grid">
              <span>项目</span>
              <span>状态</span>
              <span className="text-right">操作</span>
            </div>

            <div className="divide-y divide-[var(--hairline)]">
              {projects.map((project) => {
                const isEditing = editingProjectId === project.id;
                const renamePending = pendingAction === `rename:${project.id}`;
                const archivePending =
                  pendingAction === `archive:${project.id}`;

                return (
                  <article
                    className="grid gap-3 px-4 py-4 md:grid-cols-[minmax(0,1.5fr)_8rem_15rem] md:items-center md:gap-4"
                    key={project.id}
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="grid size-10 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)]">
                        <FolderKanban aria-hidden="true" className="size-5" />
                      </span>
                      <div className="min-w-0 flex-1">
                        {isEditing ? (
                          <Input
                            aria-label={`项目 ${project.name} 新名称`}
                            autoFocus
                            className="h-9"
                            onChange={(event) =>
                              setEditingName(event.target.value)
                            }
                            value={editingName}
                          />
                        ) : (
                          <>
                            <h2 className="truncate text-base font-semibold">
                              {project.name}
                            </h2>
                            <p className="mt-1 truncate text-xs text-[var(--muted)]">
                              {project.id}
                            </p>
                          </>
                        )}
                      </div>
                    </div>

                    <div>
                      <span
                        className={`inline-flex h-7 items-center rounded-[var(--radius-pill)] px-2.5 text-xs font-medium ${
                          project.archived
                            ? "bg-[var(--canvas-soft)] text-[var(--muted)]"
                            : "bg-[var(--success-subtle)] text-[var(--success)]"
                        }`}
                      >
                        {project.archived ? "已归档" : "运行中"}
                      </span>
                    </div>

                    <div className="flex flex-wrap justify-start gap-2 md:justify-end">
                      {isEditing ? (
                        <>
                          <Button
                            aria-label={`保存${project.name}`}
                            className="h-8 px-3"
                            disabled={!editingName.trim() || renamePending}
                            loading={renamePending}
                            onClick={() => submitRename(project)}
                            type="button"
                            variant="primary"
                          >
                            <Save aria-hidden="true" className="size-3.5" />
                            保存
                          </Button>
                          <Button
                            aria-label={`取消编辑${project.name}`}
                            className="h-8 px-3"
                            onClick={() => {
                              setEditingProjectId(null);
                              setEditingName("");
                            }}
                            type="button"
                          >
                            <X aria-hidden="true" className="size-3.5" />
                            取消
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            aria-label={`进入${project.name} 测试 Agent`}
                            className="h-8 px-3"
                            disabled={project.archived}
                            onClick={() => onOpen(project.id)}
                            type="button"
                            variant="primary"
                          >
                            <PlayCircle
                              aria-hidden="true"
                              className="size-3.5"
                            />
                            进入
                          </Button>
                          <Button
                            aria-label={`编辑${project.name}`}
                            className="h-8 px-3"
                            disabled={project.archived}
                            onClick={() => startRename(project)}
                            type="button"
                          >
                            <Edit3 aria-hidden="true" className="size-3.5" />
                            编辑
                          </Button>
                          <Button
                            aria-label={`归档${project.name}`}
                            className="h-8 px-3"
                            disabled={project.archived || archivePending}
                            loading={archivePending}
                            onClick={() => submitArchive(project)}
                            type="button"
                            variant="danger"
                          >
                            <Archive aria-hidden="true" className="size-3.5" />
                            归档
                          </Button>
                        </>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="min-w-24 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 py-2">
      <div className="text-lg font-semibold">{value}</div>
      <div className="mt-0.5 text-xs text-[var(--muted)]">{label}</div>
    </div>
  );
}

function ProjectListState({
  error,
  loading,
  projectCount,
}: {
  error?: "service";
  loading: boolean;
  projectCount: number;
}) {
  if (loading) {
    return <p className="mt-5 text-sm text-[var(--muted)]">正在加载项目…</p>;
  }

  if (error) {
    return (
      <div className="mt-5 rounded-[var(--radius-md)] border border-[var(--danger)] bg-[var(--danger-subtle)] px-4 py-3 text-sm text-[var(--danger)]">
        项目列表暂时不可用，请刷新后重试。
      </div>
    );
  }

  if (projectCount === 0) {
    return (
      <div className="mt-5 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-8 text-center">
        <p className="text-base font-semibold">暂无项目</p>
        <p className="mt-2 text-sm text-[var(--muted)]">
          创建第一个项目后即可进入测试 Agent。
        </p>
      </div>
    );
  }

  return null;
}
