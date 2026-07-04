"use client";

import { MoreHorizontal, Plus } from "lucide-react";
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
    <div className="mx-auto max-w-5xl px-6 py-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">浏览器实例</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            管理可复用的浏览器实例，登录一次后在多个测试中复用登录态
          </p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button disabled={!onCreate}>
              <Plus aria-hidden="true" className="mr-1 size-4" />
              新建实例
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>新建浏览器实例</DialogTitle>
            <DialogDescription>
              创建一个新的浏览器实例配置，用于复用登录态和浏览器状态
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
              >
                {creating ? "创建中..." : "创建"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {profiles.length === 0 ? (
        <EmptyState
          action={
            onCreate ? (
              <Button onClick={() => setCreateOpen(true)}>
                <Plus aria-hidden="true" className="mr-1 size-4" />
                新建实例
              </Button>
            ) : undefined
          }
          description="还没有浏览器实例，创建一个开始使用"
          title="暂无浏览器实例"
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>名称</TableHead>
              <TableHead>目标域名</TableHead>
              <TableHead>端口</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>登录态</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {profiles.map((profile) => (
              <TableRow key={profile.profile_id}>
                <TableCell className="font-medium">{profile.name}</TableCell>
                <TableCell className="text-[var(--muted)]">
                  {profile.target_domain || (
                    <span className="italic">未设置</span>
                  )}
                </TableCell>
                <TableCell className="text-[var(--muted)] font-mono text-xs">
                  {profile.cdp_port || "-"}
                </TableCell>
                <TableCell>{statusBadge(profile.status)}</TableCell>
                <TableCell>
                  {profile.storage_state_path ? (
                    <Badge tone="success">已登录</Badge>
                  ) : (
                    <Badge tone="neutral">未登录</Badge>
                  )}
                </TableCell>
                <TableCell className="text-[var(--muted)] text-xs">
                  {profile.created_at
                    ? new Date(profile.created_at).toLocaleDateString("zh-CN")
                    : "-"}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost">
                        <MoreHorizontal className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => openEdit(profile)}>
                        编辑
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-[var(--destructive)]"
                        onClick={() => openDelete(profile)}
                      >
                        删除
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* 编辑对话框 */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogTitle>编辑浏览器实例</DialogTitle>
          <DialogDescription>修改浏览器实例的名称和目标域名</DialogDescription>
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
              {editing ? "保存中..." : "保存"}
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
