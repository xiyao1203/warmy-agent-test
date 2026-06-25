"use client";

import type { UserResponse } from "@warmy/generated-api-client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
} from "@/components/ui/drawer";

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
  open,
  user,
}: {
  currentUser: UserResponse;
  onOpenChange: (open: boolean) => void;
  open: boolean;
  user?: UserResponse;
}) {
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
          <Button className="w-full justify-start">编辑用户</Button>
          <Button className="w-full justify-start">重置密码</Button>
          {!isCurrentUser ? (
            <Button className="w-full justify-start" variant="danger">
              {user.status === "active" ? "禁用用户" : "启用用户"}
            </Button>
          ) : (
            <p className="rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] px-3 py-2 text-xs leading-5 text-[var(--text-muted)]">
              为避免意外退出管理入口，当前账号不能在此禁用或降权。
            </p>
          )}
        </div>
      </DrawerContent>
    </Drawer>
  );
}
