"use client";

import type { SystemRole, UserResponse, UserStatus } from "@warmy/generated-api-client";
import { Search, UserPlus } from "lucide-react";
import { useMemo, useState } from "react";

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

import { UserDrawer } from "./user-drawer";

type UserManagementProps = {
  currentUser: UserResponse;
  error?: "permission" | "service";
  loading?: boolean;
  nextCursor?: string | null;
  users?: UserResponse[];
};

const roleLabels: Record<SystemRole, string> = {
  developer: "开发",
  reviewer: "审核",
  super_admin: "超级管理员",
  tester: "测试",
  viewer: "只读",
};

const statusLabels: Record<UserStatus, string> = {
  active: "活跃",
  disabled: "已禁用",
};

export function UserManagement({
  currentUser,
  error,
  loading = false,
  nextCursor,
  users = [],
}: UserManagementProps) {
  const [query, setQuery] = useState("");
  const [role, setRole] = useState<SystemRole | "all">("all");
  const [status, setStatus] = useState<UserStatus | "all">("all");
  const [selectedUser, setSelectedUser] = useState<UserResponse>();
  const filteredUsers = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    return users.filter((user) => {
      const matchesQuery =
        !normalized ||
        user.display_name.toLocaleLowerCase().includes(normalized) ||
        user.email.toLocaleLowerCase().includes(normalized);
      return (
        matchesQuery &&
        (role === "all" || user.role === role) &&
        (status === "all" || user.status === status)
      );
    });
  }, [query, role, status, users]);

  if (loading) return <StatusPanel title="正在加载用户…" />;
  if (error === "permission") {
    return (
      <StatusPanel
        description="用户管理只对超级管理员开放。"
        title="你没有用户管理权限"
      />
    );
  }
  if (error === "service") {
    return (
      <StatusPanel
        description="服务暂时没有响应，请稍后刷新重试。"
        title="用户列表暂时不可用"
      />
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">用户管理</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            管理内部账号、系统角色和登录状态。
          </p>
        </div>
        <Button variant="primary">
          <UserPlus aria-hidden="true" className="mr-2 size-4" />
          创建用户
        </Button>
      </header>

      <section className="grid grid-cols-4 border-b border-[var(--border)] py-4 text-sm max-[900px]:grid-cols-2 max-[900px]:gap-4">
        <Summary label="当前页用户" value={users.length} />
        <Summary
          label="活跃"
          value={users.filter((user) => user.status === "active").length}
        />
        <Summary
          label="已禁用"
          value={users.filter((user) => user.status === "disabled").length}
        />
        <Summary
          label="需改密"
          value={users.filter((user) => user.must_change_password).length}
        />
      </section>

      <div className="flex flex-wrap items-center gap-2 py-4">
        <label className="relative min-w-64 flex-1">
          <Search
            aria-hidden="true"
            className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <Input
            className="pl-9"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索姓名或邮箱"
            value={query}
          />
        </label>
        <select
          aria-label="按角色筛选"
          className="h-9 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 text-sm"
          onChange={(event) => setRole(event.target.value as SystemRole | "all")}
          value={role}
        >
          <option value="all">全部角色</option>
          {Object.entries(roleLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select
          aria-label="按状态筛选"
          className="h-9 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 text-sm"
          onChange={(event) =>
            setStatus(event.target.value as UserStatus | "all")
          }
          value={status}
        >
          <option value="all">全部状态</option>
          <option value="active">活跃</option>
          <option value="disabled">已禁用</option>
        </select>
      </div>

      <section className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {!users.length ? (
          <EmptyState
            description="创建第一个内部账号后，用户会显示在这里。"
            title="暂无用户"
          />
        ) : !filteredUsers.length ? (
          <EmptyState
            description="尝试修改关键词、角色或状态筛选。"
            title="没有匹配的用户"
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>用户</TableHead>
                <TableHead>系统角色</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>登录策略</TableHead>
                <TableHead className="w-20 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.map((user) => (
                <TableRow
                  className="hover:bg-[var(--surface-subtle)]"
                  key={user.id}
                >
                  <TableCell>
                    <p className="font-medium">{user.display_name}</p>
                    <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                      {user.email}
                    </p>
                  </TableCell>
                  <TableCell>
                    <Badge tone={user.role === "super_admin" ? "accent" : "neutral"}>
                      {roleLabels[user.role]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge tone={user.status === "active" ? "success" : "danger"}>
                      {statusLabels[user.status]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {user.must_change_password ? (
                      <Badge tone="warning">需改密</Badge>
                    ) : (
                      <span className="text-[var(--text-muted)]">正常</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <button
                      aria-label={`查看${user.display_name}`}
                      className="rounded-[var(--radius-sm)] px-2 py-1 text-sm text-[var(--accent)] hover:bg-[var(--accent-subtle)]"
                      onClick={() => setSelectedUser(user)}
                      type="button"
                    >
                      查看
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
        {nextCursor ? (
          <div className="border-t border-[var(--border)] px-4 py-3 text-right text-xs text-[var(--text-muted)]">
            后端还有更多用户，下一阶段接入游标翻页。
          </div>
        ) : null}
      </section>

      <UserDrawer
        currentUser={currentUser}
        onOpenChange={(open) => {
          if (!open) setSelectedUser(undefined);
        }}
        open={Boolean(selectedUser)}
        user={selectedUser}
      />
    </div>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div className="border-r border-[var(--border)] px-4 first:pl-0 last:border-r-0">
      <p className="text-xs text-[var(--text-muted)]">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function StatusPanel({
  description,
  title,
}: {
  description?: string;
  title: string;
}) {
  return (
    <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
      <div>
        <h1 className="text-base font-semibold">{title}</h1>
        {description ? (
          <p className="mt-2 text-sm text-[var(--text-muted)]">{description}</p>
        ) : null}
      </div>
    </div>
  );
}
