"use client";

import type {
  SystemRole,
  UpdateUserRequest,
  UserResponse,
} from "@warmy/generated-api-client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
} from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";

const editSchema = z.object({
  display_name: z.string().trim().min(1, "请输入姓名"),
  email: z.email("请输入有效的邮箱地址"),
  role: z.enum(["super_admin", "developer", "tester", "reviewer", "viewer"]),
});

const roleLabels: Record<SystemRole, string> = {
  developer: "开发",
  reviewer: "审核",
  super_admin: "超级管理员",
  tester: "测试",
  viewer: "只读",
} as const;

export function UserDrawer({
  currentUser,
  onDelete,
  onEdit,
  onOpenChange,
  onResetPassword,
  onToggleStatus,
  open,
  user,
}: {
  currentUser: UserResponse;
  onDelete: (userId: string) => Promise<unknown>;
  onEdit: (userId: string, payload: UpdateUserRequest) => Promise<unknown>;
  onOpenChange: (open: boolean) => void;
  onResetPassword: (userId: string, password: string) => Promise<unknown>;
  onToggleStatus: (userId: string, enabled: boolean) => Promise<unknown>;
  open: boolean;
  user?: UserResponse;
}) {
  const [action, setAction] = useState<"delete" | "edit" | "reset" | "status">();
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const {
    formState: { errors: editErrors, isSubmitting: editSubmitting },
    handleSubmit: handleEditSubmit,
    register: registerEdit,
    reset: resetEdit,
    setError: setEditError,
  } = useForm<UpdateUserRequest>();

  if (!user) return null;
  const isCurrentUser = currentUser.id === user.id;

  function openEdit() {
    resetEdit({
      display_name: user!.display_name,
      email: user!.email,
      role: user!.role,
    });
    setError("");
    setAction("edit");
  }

  async function submitEdit(values: UpdateUserRequest) {
    setPending(true);
    setError("");
    const result = editSchema.safeParse(values);
    if (!result.success) {
      for (const issue of result.error.issues) {
        const field = issue.path[0] as keyof UpdateUserRequest;
        setEditError(field, { message: issue.message });
      }
      setPending(false);
      return;
    }

    try {
      await onEdit(user!.id, result.data);
      setAction(undefined);
    } catch {
      setError("保存失败，请检查输入后重试。");
    } finally {
      setPending(false);
    }
  }

  return (
    <Drawer onOpenChange={onOpenChange} open={open}>
      <DrawerContent>
        <DrawerTitle className="pr-10 text-base font-semibold">
          用户详情
        </DrawerTitle>
        <DrawerDescription className="mt-1 text-sm text-[var(--text-muted)]">
          查看身份、角色和账号状态。
        </DrawerDescription>

        <div className="mt-6 flex items-center gap-3 border-b border-[var(--border)] pb-5">
          <span className="flex size-10 items-center justify-center rounded-full bg-[var(--accent-subtle)] text-sm font-semibold text-[var(--accent-text)]">
            {user.display_name.slice(0, 1).toUpperCase()}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="truncate text-sm font-semibold">
                {user.display_name}
              </p>
              {isCurrentUser ? <Badge tone="accent">当前登录账号</Badge> : null}
            </div>
            <p className="mt-1 truncate text-sm text-[var(--text-muted)]">
              {user.email}
            </p>
          </div>
        </div>

        <dl className="grid grid-cols-[7rem_1fr] gap-y-3 border-b border-[var(--border)] py-5 text-sm">
          <dt className="text-[var(--text-muted)]">系统角色</dt>
          <dd>{roleLabels[user.role]}</dd>
          <dt className="text-[var(--text-muted)]">账号状态</dt>
          <dd>{user.status === "active" ? "活跃" : "已禁用"}</dd>
          <dt className="text-[var(--text-muted)]">登录策略</dt>
          <dd>{user.must_change_password ? "下次登录需修改密码" : "正常"}</dd>
          <dt className="text-[var(--text-muted)]">用户 ID</dt>
          <dd className="break-all font-mono text-xs">{user.id}</dd>
        </dl>

        <div className="mt-5 space-y-2">
          <Button
            className="w-full justify-start"
            onClick={openEdit}
          >
            编辑用户
          </Button>
          <Button
            className="w-full justify-start"
            onClick={() => {
              setAction("reset");
              setError("");
            }}
          >
            重置密码
          </Button>
          {!isCurrentUser ? (
            <>
              <Button
                className="w-full justify-start"
                onClick={() => {
                  setAction("status");
                  setError("");
                }}
                variant="danger"
              >
                {user.status === "active" ? "禁用用户" : "启用用户"}
              </Button>
              <Button
                className="w-full justify-start"
                onClick={() => {
                  setAction("delete");
                  setError("");
                }}
                variant="danger"
              >
                删除用户
              </Button>
            </>
          ) : (
            <p className="rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] px-3 py-2 text-xs leading-5 text-[var(--text-muted)]">
              为避免意外退出管理入口，当前账号不能在此禁用或降权。
            </p>
          )}
        </div>
      </DrawerContent>
      <Dialog onOpenChange={(value) => !value && setAction(undefined)} open={Boolean(action)}>
        <DialogContent>
          {action === "edit" ? (
            <>
              <DialogTitle>编辑用户</DialogTitle>
              <DialogDescription>修改用户姓名、邮箱或系统角色。</DialogDescription>
              <form className="mt-5 space-y-4" onSubmit={handleEditSubmit(submitEdit)}>
                {error ? (
                  <p className="rounded-[var(--radius-sm)] bg-[var(--danger-subtle)] px-3 py-2 text-sm text-[var(--danger)]" role="alert">
                    {error}
                  </p>
                ) : null}
                <EditField error={editErrors.display_name?.message} htmlFor="drawer-edit-name" label="姓名">
                  <Input autoFocus id="drawer-edit-name" {...registerEdit("display_name")} />
                </EditField>
                <EditField error={editErrors.email?.message} htmlFor="drawer-edit-email" label="邮箱">
                  <Input id="drawer-edit-email" type="email" {...registerEdit("email")} />
                </EditField>
                <EditField error={editErrors.role?.message} htmlFor="drawer-edit-role" label="系统角色">
                  <select
                    className="h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 text-sm"
                    id="drawer-edit-role"
                    {...registerEdit("role")}
                  >
                    {(
                      [
                        ["developer", "开发"],
                        ["tester", "测试"],
                        ["reviewer", "审核"],
                        ["viewer", "只读"],
                        ["super_admin", "超级管理员"],
                      ] as Array<[SystemRole, string]>
                    ).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </EditField>
                <div className="flex justify-end gap-2 pt-2">
                  <Button onClick={() => setAction(undefined)} type="button">
                    取消
                  </Button>
                  <Button disabled={editSubmitting || pending} type="submit" variant="primary">
                    {editSubmitting || pending ? "正在保存…" : "保存修改"}
                  </Button>
                </div>
              </form>
            </>
          ) : action === "delete" ? (
            <>
              <DialogTitle>删除 {user.display_name}</DialogTitle>
              <DialogDescription>
                删除后该用户将无法登录。如果用户有历史操作记录，系统会改为禁用而非物理删除。
                此操作不可撤销。
              </DialogDescription>
              {error ? (
                <p className="mt-3 text-sm text-[var(--danger)]" role="alert">
                  {error}
                </p>
              ) : null}
              <div className="mt-5 flex justify-end gap-2">
                <Button onClick={() => setAction(undefined)} type="button">
                  取消
                </Button>
                <Button
                  disabled={pending}
                  onClick={async () => {
                    setPending(true);
                    setError("");
                    try {
                      await onDelete(user.id);
                      setAction(undefined);
                    } catch {
                      setError("删除失败，请刷新数据后重试。");
                    } finally {
                      setPending(false);
                    }
                  }}
                  type="button"
                  variant="danger"
                >
                  {pending ? "正在处理…" : "确认删除用户"}
                </Button>
              </div>
            </>
          ) : (
            <>
              <DialogTitle>
                {action === "reset"
                  ? `重置 ${user.display_name} 的密码`
                  : `${user.status === "active" ? "禁用" : "启用"} ${user.display_name}`}
              </DialogTitle>
              <DialogDescription>
                {action === "reset"
                  ? "密码重置会立即撤销该用户的所有有效 Session，并要求使用新密码登录。"
                  : user.status === "active"
                    ? "禁用后用户将无法登录，现有 Session 会立即失效。"
                    : "启用后用户可以重新登录，但不会自动恢复已移除的项目权限。"}
              </DialogDescription>
              {action === "reset" ? (
                <div className="mt-4">
                  <label className="mb-1.5 block text-sm font-medium" htmlFor="reset-password">
                    新密码
                  </label>
                  <Input
                    autoComplete="new-password"
                    autoFocus
                    id="reset-password"
                    onChange={(event) => setPassword(event.target.value)}
                    type="password"
                    value={password}
                  />
                </div>
              ) : null}
              {error ? (
                <p className="mt-3 text-sm text-[var(--danger)]" role="alert">
                  {error}
                </p>
              ) : null}
              <div className="mt-5 flex justify-end gap-2">
                <Button onClick={() => setAction(undefined)} type="button">
                  取消
                </Button>
                <Button
                  disabled={pending || (action === "reset" && password.length < 12)}
                  onClick={async () => {
                    setPending(true);
                    setError("");
                    try {
                      if (action === "reset") {
                        await onResetPassword(user.id, password);
                        setPassword("");
                      } else {
                        await onToggleStatus(user.id, user.status !== "active");
                      }
                      setAction(undefined);
                    } catch {
                      setError("操作失败，请刷新数据后重试。");
                    } finally {
                      setPending(false);
                    }
                  }}
                  type="button"
                  variant={action === "status" ? "danger" : "primary"}
                >
                  {pending
                    ? "正在处理…"
                    : action === "reset"
                      ? "确认重置密码"
                      : user.status === "active"
                        ? "确认禁用用户"
                        : "确认启用用户"}
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </Drawer>
  );
}

function EditField({
  children,
  error,
  htmlFor,
  label,
}: {
  children: React.ReactNode;
  error?: string;
  htmlFor: string;
  label: string;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {error ? <p className="mt-1 text-xs text-[var(--danger)]">{error}</p> : null}
    </div>
  );
}
"use client";

import type { UserResponse } from "@warmy/generated-api-client";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
} from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";

const roleLabels = {
  developer: "开发",
  reviewer: "审核",
  super_admin: "超级管理员",
  tester: "测试",
  viewer: "只读",
} as const;

export function UserDrawer({
  currentUser,
  onOpenChange,
  onResetPassword,
  onToggleStatus,
  open,
  user,
}: {
  currentUser: UserResponse;
  onOpenChange: (open: boolean) => void;
  onResetPassword: (userId: string, password: string) => Promise<unknown>;
  onToggleStatus: (userId: string, enabled: boolean) => Promise<unknown>;
  open: boolean;
  user?: UserResponse;
}) {
  const [action, setAction] = useState<"reset" | "status">();
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  if (!user) return null;
  const isCurrentUser = currentUser.id === user.id;

  return (
    <Drawer onOpenChange={onOpenChange} open={open}>
      <DrawerContent>
        <DrawerTitle className="pr-10 text-base font-semibold">
          用户详情
        </DrawerTitle>
        <DrawerDescription className="mt-1 text-sm text-[var(--text-muted)]">
          查看身份、角色和账号状态。
        </DrawerDescription>

        <div className="mt-6 flex items-center gap-3 border-b border-[var(--border)] pb-5">
          <span className="flex size-10 items-center justify-center rounded-full bg-[var(--accent-subtle)] text-sm font-semibold text-[var(--accent-text)]">
            {user.display_name.slice(0, 1).toUpperCase()}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="truncate text-sm font-semibold">
                {user.display_name}
              </p>
              {isCurrentUser ? <Badge tone="accent">当前登录账号</Badge> : null}
            </div>
            <p className="mt-1 truncate text-sm text-[var(--text-muted)]">
              {user.email}
            </p>
          </div>
        </div>

        <dl className="grid grid-cols-[7rem_1fr] gap-y-3 border-b border-[var(--border)] py-5 text-sm">
          <dt className="text-[var(--text-muted)]">系统角色</dt>
          <dd>{roleLabels[user.role]}</dd>
          <dt className="text-[var(--text-muted)]">账号状态</dt>
          <dd>{user.status === "active" ? "活跃" : "已禁用"}</dd>
          <dt className="text-[var(--text-muted)]">登录策略</dt>
          <dd>{user.must_change_password ? "下次登录需修改密码" : "正常"}</dd>
          <dt className="text-[var(--text-muted)]">用户 ID</dt>
          <dd className="break-all font-mono text-xs">{user.id}</dd>
        </dl>

        <div className="mt-5 space-y-2">
          <Button
            className="w-full justify-start"
            onClick={() => {
              setAction("reset");
              setError("");
            }}
          >
            重置密码
          </Button>
          {!isCurrentUser ? (
            <Button
              className="w-full justify-start"
              onClick={() => {
                setAction("status");
                setError("");
              }}
              variant="danger"
            >
              {user.status === "active" ? "禁用用户" : "启用用户"}
            </Button>
          ) : (
            <p className="rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] px-3 py-2 text-xs leading-5 text-[var(--text-muted)]">
              为避免意外退出管理入口，当前账号不能在此禁用或降权。
            </p>
          )}
        </div>
      </DrawerContent>
      <Dialog onOpenChange={(value) => !value && setAction(undefined)} open={Boolean(action)}>
        <DialogContent>
          <DialogTitle>
            {action === "reset"
              ? `重置 ${user.display_name} 的密码`
              : `${user.status === "active" ? "禁用" : "启用"} ${user.display_name}`}
          </DialogTitle>
          <DialogDescription>
            {action === "reset"
              ? "密码重置会立即撤销该用户的所有有效 Session，并要求使用新密码登录。"
              : user.status === "active"
                ? "禁用后用户将无法登录，现有 Session 会立即失效。"
                : "启用后用户可以重新登录，但不会自动恢复已移除的项目权限。"}
          </DialogDescription>
          {action === "reset" ? (
            <div className="mt-4">
              <label className="mb-1.5 block text-sm font-medium" htmlFor="reset-password">
                新密码
              </label>
              <Input
                autoComplete="new-password"
                autoFocus
                id="reset-password"
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                value={password}
              />
            </div>
          ) : null}
          {error ? (
            <p className="mt-3 text-sm text-[var(--danger)]" role="alert">
              {error}
            </p>
          ) : null}
          <div className="mt-5 flex justify-end gap-2">
            <Button onClick={() => setAction(undefined)} type="button">
              取消
            </Button>
            <Button
              disabled={pending || (action === "reset" && password.length < 12)}
              onClick={async () => {
                setPending(true);
                setError("");
                try {
                  if (action === "reset") {
                    await onResetPassword(user.id, password);
                    setPassword("");
                  } else {
                    await onToggleStatus(user.id, user.status !== "active");
                  }
                  setAction(undefined);
                } catch {
                  setError("操作失败，请刷新数据后重试。");
                } finally {
                  setPending(false);
                }
              }}
              type="button"
              variant={action === "status" ? "danger" : "primary"}
            >
              {pending
                ? "正在处理…"
                : action === "reset"
                  ? "确认重置密码"
                  : user.status === "active"
                    ? "确认禁用用户"
                    : "确认启用用户"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Drawer>
  );
}
