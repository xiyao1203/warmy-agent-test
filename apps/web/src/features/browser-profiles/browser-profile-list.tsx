"use client";

import {
  ClipboardCheck,
  MoreHorizontal,
  PlayCircle,
  Plus,
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
  projectId,
}: BrowserProfileListProps) {
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createDomain, setCreateDomain] = useState("");
  const [creating, setCreating] = useState(false);

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
    try {
      await onCreate({
        name: createName.trim(),
        target_domain: createDomain.trim() || undefined,
      });
      setCreateOpen(false);
      setCreateName("");
      setCreateDomain("");
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
            新建实例并保存登录态，测试计划选择后，浏览器用例会在运行时复用。
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
              创建后用于保存登录状态，并在测试计划中选择复用。
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
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button onClick={() => setCreateOpen(false)} variant="ghost">
                取消
              </Button>
              <Button
                disabled={!createName.trim() || creating}
                onClick={handleCreate}
                variant="primary"
              >
                {creating ? "创建中..." : "新建浏览器实例"}
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
          description="人工登录后保存状态"
          icon={<UserCheck aria-hidden="true" className="size-4" />}
          label="2. 保存登录态"
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
          description="先新建一个浏览器实例，再在测试计划的执行配置中选择它。"
          title="暂无浏览器实例"
        />
      ) : (
        <section className="overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
          <Table className="w-full min-w-[920px] table-fixed">
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead className="w-[280px]">实例信息</TableHead>
                <TableHead className="w-48">目标域名</TableHead>
                <TableHead className="w-24 text-center">端口</TableHead>
                <TableHead className="w-24 text-center">状态</TableHead>
                <TableHead className="w-28 text-center">登录态</TableHead>
                <TableHead className="w-32 text-center">创建时间</TableHead>
                <TableHead className="w-40 text-right">下一步</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {profiles.map((profile) => (
                <TableRow key={profile.profile_id}>
                  <TableCell>
                    <div className="min-w-0">
                      <p className="truncate font-medium">{profile.name}</p>
                      <p className="mt-0.5 truncate text-xs text-[var(--muted)]">
                        测试计划选择后，浏览器用例会复用这个实例
                      </p>
                    </div>
                  </TableCell>
                  <TableCell className="text-[var(--muted)]">
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
                    ) : (
                      <Badge tone="neutral">未登录</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-center text-xs text-[var(--muted)]">
                    {profile.created_at
                      ? new Date(profile.created_at).toLocaleDateString("zh-CN")
                      : "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button asChild className="px-3" variant="secondary">
                        <Link href={`/projects/${projectId}/test-plans`}>
                          去配置
                        </Link>
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            aria-label={`管理${profile.name}`}
                            className="w-9 px-0"
                            variant="ghost"
                          >
                            <MoreHorizontal className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEdit(profile)}>
                            设置实例
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-[var(--destructive)]"
                            onClick={() => openDelete(profile)}
                          >
                            删除
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
            」吗？此操作不会删除已保存的浏览器数据目录。
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
