"use client";

import {
  ClipboardCheck,
  MoreHorizontal,
  PlayCircle,
  Plus,
  Square,
  Trash2,
  UserCheck,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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

import type { BrowserProfile } from "./api";

type BrowserProfileListProps = {
  profiles?: BrowserProfile[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: {
    name: string;
    target_domain?: string;
  }) => Promise<BrowserProfile>;
  onUpdate?: (
    profileId: string,
    payload: { name?: string; target_domain?: string },
  ) => Promise<BrowserProfile>;
  onDelete?: (profileId: string) => Promise<void>;
  onStart?: (
    profileId: string,
    payload: { login_url?: string },
  ) => Promise<BrowserProfile>;
  onCompleteLogin?: (
    profileId: string,
    payload: { stop_after_save?: boolean },
  ) => Promise<BrowserProfile>;
  onStop?: (profileId: string) => Promise<BrowserProfile>;
  projectId: string;
};

function statusBadge(status: string) {
  const map: Record<
    string,
    { label: string; tone: "success" | "neutral" | "danger" }
  > = {
    running: { label: "运行中", tone: "success" },
    stopped: { label: "已停止", tone: "neutral" },
    error: { label: "异常", tone: "danger" },
  };
  const info = map[status] ?? { label: status, tone: "neutral" as const };
  return <Badge tone={info.tone}>{info.label}</Badge>;
}

export function BrowserProfileList({
  profiles = [],
  error,
  loading = false,
  onCreate,
  onUpdate,
  onDelete,
  onStart,
  onCompleteLogin,
  onStop,
  projectId,
}: BrowserProfileListProps) {
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createDomain, setCreateDomain] = useState("");
  const [createLoginUrl, setCreateLoginUrl] = useState("");
  const [launchAfterCreate, setLaunchAfterCreate] = useState(true);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [busyProfileId, setBusyProfileId] = useState("");
  const [actionError, setActionError] = useState("");

  const [editOpen, setEditOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<BrowserProfile | null>(
    null,
  );
  const [editName, setEditName] = useState("");
  const [editDomain, setEditDomain] = useState("");
  const [editing, setEditing] = useState(false);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletingProfile, setDeletingProfile] = useState<BrowserProfile | null>(
    null,
  );
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  async function handleCreate() {
    if (!onCreate || !createName.trim()) return;
    setCreating(true);
    setCreateError("");
    try {
      const created = await onCreate({
        name: createName.trim(),
        target_domain: createDomain.trim() || undefined,
      });
      if (launchAfterCreate && onStart) {
        await onStart(created.profile_id, {
          login_url: createLoginUrl.trim() || createDomain.trim() || undefined,
        });
      }
      setCreateOpen(false);
      setCreateName("");
      setCreateDomain("");
      setCreateLoginUrl("");
      setLaunchAfterCreate(true);
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "创建或启动浏览器失败",
      );
    } finally {
      setCreating(false);
    }
  }

  function openEdit(profile: BrowserProfile) {
    setEditingProfile(profile);
    setEditName(profile.name);
    setEditDomain(profile.target_domain);
    setEditOpen(true);
  }

  async function handleEdit() {
    if (!onUpdate || !editingProfile) return;
    setEditing(true);
    try {
      await onUpdate(editingProfile.profile_id, {
        name: editName.trim() || undefined,
        target_domain: editDomain.trim() || undefined,
      });
      setEditOpen(false);
      setEditingProfile(null);
    } finally {
      setEditing(false);
    }
  }

  function openDelete(profile: BrowserProfile) {
    setDeletingProfile(profile);
    setDeleteError("");
    setDeleteOpen(true);
  }

  async function handleDelete() {
    if (!onDelete || !deletingProfile) return;
    setDeleting(true);
    try {
      await onDelete(deletingProfile.profile_id);
      setDeleteOpen(false);
      setDeletingProfile(null);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "删除失败");
    } finally {
      setDeleting(false);
    }
  }

  async function handleStart(profile: BrowserProfile) {
    if (!onStart) return;
    setBusyProfileId(profile.profile_id);
    setActionError("");
    try {
      await onStart(profile.profile_id, {
        login_url: profile.target_domain || undefined,
      });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "启动浏览器失败");
    } finally {
      setBusyProfileId("");
    }
  }

  async function handleCompleteLogin(profile: BrowserProfile) {
    if (!onCompleteLogin) return;
    setBusyProfileId(profile.profile_id);
    setActionError("");
    try {
      await onCompleteLogin(profile.profile_id, { stop_after_save: true });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "保存登录状态失败");
    } finally {
      setBusyProfileId("");
    }
  }

  async function handleStop(profile: BrowserProfile) {
    if (!onStop) return;
    setBusyProfileId(profile.profile_id);
    setActionError("");
    try {
      await onStop(profile.profile_id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "停止浏览器失败");
    } finally {
      setBusyProfileId("");
    }
  }

  if (loading) {
    return <ProfileListSkeleton />;
  }
  if (error === "not-found") {
    return (
      <div className="flex min-h-[calc(100vh-3rem)] items-center justify-center text-sm">
        <p className="text-[var(--muted)]">项目不存在或无权访问</p>
      </div>
    );
  }
  if (error === "service") {
    return (
      <div className="flex min-h-[calc(100vh-3rem)] items-center justify-center text-sm">
        <p className="text-[var(--muted)]">浏览器实例列表暂时不可用</p>
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <div className="mb-5 flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">浏览器实例</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            新建实例后启动浏览器，人工登录并确认保存；测试计划选择后，Codex
            浏览器用例会复用这个独立浏览器目录。
          </p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button disabled={!onCreate} variant="primary">
              <Plus aria-hidden="true" className="mr-1 size-4" />
              新建浏览器实例
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>新建浏览器实例</DialogTitle>
            <DialogDescription>
              填好名称和登录地址后，可以立即启动浏览器完成登录。
            </DialogDescription>
            <div className="mt-4 space-y-3">
              <label className="block">
                <span className="text-sm font-medium">名称 *</span>
                <Input
                  className="mt-1"
                  onChange={(e) => setCreateName(e.target.value)}
                  placeholder="如：公司内网-管理员"
                  value={createName}
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium">目标域名</span>
                <Input
                  className="mt-1"
                  onChange={(e) => setCreateDomain(e.target.value)}
                  placeholder="如：app.example.com"
                  value={createDomain}
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium">登录地址</span>
                <Input
                  className="mt-1"
                  onChange={(e) => setCreateLoginUrl(e.target.value)}
                  placeholder="如：https://app.example.com/login"
                  value={createLoginUrl}
                />
              </label>
              <label className="flex items-start gap-2 text-sm">
                <input
                  checked={launchAfterCreate}
                  className="mt-1"
                  onChange={(e) => setLaunchAfterCreate(e.target.checked)}
                  type="checkbox"
                />
                <span>
                  创建后立即启动浏览器登录
                  <span className="block text-xs text-[var(--muted)]">
                    浏览器会用独立用户目录打开，登录完成后回到列表点击“我已完成登录”。
                  </span>
                </span>
              </label>
            </div>
            {createError ? (
              <p className="mt-3 text-sm text-[var(--danger)]">{createError}</p>
            ) : null}
            <div className="mt-5 flex justify-end gap-2">
              <Button onClick={() => setCreateOpen(false)} variant="ghost">
                取消
              </Button>
              <Button
                disabled={!createName.trim() || creating}
                onClick={handleCreate}
                variant="primary"
              >
                {creating
                  ? launchAfterCreate
                    ? "创建并启动中..."
                    : "创建中..."
                  : launchAfterCreate
                    ? "创建并启动登录"
                    : "新建浏览器实例"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <section className="mb-5 grid gap-3 md:grid-cols-4">
        <FlowCard
          description="创建独立用户目录"
          icon={<Plus aria-hidden="true" className="size-4" />}
          label="1. 新建实例"
        />
        <FlowCard
          description="启动浏览器人工登录"
          icon={<UserCheck aria-hidden="true" className="size-4" />}
          label="2. 启动并登录"
        />
        <FlowCard
          description="执行配置里选择实例"
          href={`/projects/${projectId}/test-plans`}
          icon={<ClipboardCheck aria-hidden="true" className="size-4" />}
          label="3. 配置测试计划"
        />
        <FlowCard
          description="浏览器用例自动复用"
          href={`/projects/${projectId}/runs`}
          icon={<PlayCircle aria-hidden="true" className="size-4" />}
          label="4. 启动测试执行"
        />
      </section>

      <section className="mb-5 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-4">
        <h2 className="text-sm font-semibold">这些实例用在哪儿</h2>
        <div className="mt-2 grid gap-3 text-sm text-[var(--muted)] md:grid-cols-3">
          <p>
            <span className="font-medium text-[var(--ink)]">测试计划：</span>
            在执行配置里选择浏览器实例。
          </p>
          <p>
            <span className="font-medium text-[var(--ink)]">浏览器用例：</span>
            Codex 浏览器执行会复用实例的用户目录。
          </p>
          <p>
            <span className="font-medium text-[var(--ink)]">测试执行：</span>
            运行时自动带上已选实例，不需要每次重新登录。
          </p>
        </div>
      </section>

      {actionError ? (
        <div className="mb-4 rounded border border-[var(--danger)] bg-[var(--danger-subtle)] px-4 py-3 text-sm text-[var(--danger)]">
          {actionError}
        </div>
      ) : null}

      {profiles.length === 0 ? (
        <EmptyState
          action={
            onCreate ? (
              <Button onClick={() => setCreateOpen(true)} variant="primary">
                <Plus aria-hidden="true" className="mr-1 size-4" />
                新建浏览器实例
              </Button>
            ) : undefined
          }
          description="先新建浏览器实例，启动浏览器完成登录，再在测试计划的执行配置中选择它。"
          title="暂无浏览器实例"
        />
      ) : (
        <section className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
          <Table className="w-full table-fixed">
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead className="w-[24%]">实例</TableHead>
                <TableHead className="w-[17%]">目标域名</TableHead>
                <TableHead className="w-[8%]">端口</TableHead>
                <TableHead className="w-[9%]">状态</TableHead>
                <TableHead className="w-[10%]">登录态</TableHead>
                <TableHead className="w-[10%]">创建</TableHead>
                <TableHead className="w-[22%]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {profiles.map((profile) => (
                <TableRow key={profile.profile_id}>
                  <TableCell className="min-w-0">
                    <div className="mx-auto min-w-0 max-w-full text-center">
                      <p className="truncate font-medium">{profile.name}</p>
                      <p className="mt-0.5 truncate text-xs text-[var(--muted)]">
                        计划选择后自动复用
                      </p>
                    </div>
                  </TableCell>
                  <TableCell className="truncate text-[var(--muted)]">
                    {profile.target_domain || (
                      <span className="italic">未设置</span>
                    )}
                  </TableCell>
                  <TableCell className="text-center font-mono text-xs text-[var(--muted)]">
                    {profile.cdp_port || "-"}
                  </TableCell>
                  <TableCell className="text-center">
                    {statusBadge(profile.status)}
                  </TableCell>
                  <TableCell className="text-center">
                    {profile.storage_state_path ? (
                      <Badge tone="success">已登录</Badge>
                    ) : profile.last_login_at ? (
                      <Badge tone="success">已确认登录</Badge>
                    ) : profile.status === "running" ? (
                      <Badge tone="warning">登录中</Badge>
                    ) : (
                      <Badge tone="neutral">未确认</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-center text-xs text-[var(--muted)]">
                    {profile.created_at
                      ? new Date(profile.created_at).toLocaleDateString("zh-CN")
                      : "-"}
                  </TableCell>
                  <TableCell>
                    <div className="mx-auto flex w-fit max-w-full items-center justify-center gap-1.5">
                      {profile.status === "running" ? (
                        <>
                          <Button
                            className="h-8 px-2.5 text-xs"
                            disabled={
                              busyProfileId === profile.profile_id ||
                              !onCompleteLogin
                            }
                            onClick={() => void handleCompleteLogin(profile)}
                            variant="primary"
                          >
                            我已完成登录
                          </Button>
                          <Button
                            aria-label={`停止浏览器 ${profile.name}`}
                            className="h-8 px-2.5 text-xs"
                            disabled={
                              busyProfileId === profile.profile_id || !onStop
                            }
                            onClick={() => void handleStop(profile)}
                            variant="secondary"
                          >
                            <Square
                              aria-hidden="true"
                              className="mr-1 size-3"
                            />
                            停止
                          </Button>
                        </>
                      ) : (
                        <Button
                          className="h-8 px-2.5 text-xs"
                          disabled={
                            busyProfileId === profile.profile_id || !onStart
                          }
                          onClick={() => void handleStart(profile)}
                          variant="primary"
                        >
                          <PlayCircle
                            aria-hidden="true"
                            className="mr-1 size-4"
                          />
                          启动并登录
                        </Button>
                      )}
                      <Button
                        asChild
                        className="h-8 px-2.5 text-xs"
                        variant="secondary"
                      >
                        <Link href={`/projects/${projectId}/test-plans`}>
                          配置计划
                        </Link>
                      </Button>
                      <Button
                        aria-label={`删除浏览器实例 ${profile.name}`}
                        className="h-8 w-8 px-0"
                        disabled={!onDelete}
                        onClick={() => openDelete(profile)}
                        variant="ghost"
                      >
                        <Trash2
                          aria-hidden="true"
                          className="size-4 text-[var(--danger)]"
                        />
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            aria-label={`管理${profile.name}`}
                            className="h-8 w-8 px-0"
                            variant="ghost"
                          >
                            <MoreHorizontal className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEdit(profile)}>
                            设置实例
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
      )}

      {/* 编辑对话框 */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogTitle>编辑浏览器实例</DialogTitle>
          <DialogDescription>
            修改浏览器实例的名称和适用域名。
          </DialogDescription>
          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="text-sm font-medium">名称</span>
              <Input
                className="mt-1"
                onChange={(e) => setEditName(e.target.value)}
                value={editName}
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium">目标域名</span>
              <Input
                className="mt-1"
                onChange={(e) => setEditDomain(e.target.value)}
                placeholder="如：app.example.com"
                value={editDomain}
              />
            </label>
          </div>
          <div className="mt-5 flex justify-end gap-2">
            <Button onClick={() => setEditOpen(false)} variant="ghost">
              取消
            </Button>
            <Button disabled={!editName.trim() || editing} onClick={handleEdit}>
              {editing ? "保存中..." : "保存设置"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogTitle>删除浏览器实例</DialogTitle>
          <DialogDescription>
            确定要删除「{deletingProfile?.name}
            」吗？会从平台列表移除，并停止正在运行的浏览器；已保存的数据目录不会被删除。
          </DialogDescription>
          {deleteError ? (
            <p className="mt-2 text-sm text-[var(--destructive)]">
              {deleteError}
            </p>
          ) : null}
          <div className="mt-5 flex justify-end gap-2">
            <Button onClick={() => setDeleteOpen(false)} variant="ghost">
              取消
            </Button>
            <Button disabled={deleting} onClick={handleDelete} variant="danger">
              {deleting ? "删除中..." : "删除"}
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

function ProfileListSkeleton() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-6">
      <div className="mb-5">
        <Skeleton className="mb-2 h-6 w-40" />
        <Skeleton className="h-4 w-72" />
      </div>
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    </div>
  );
}
