"use client";

import type {
  CreateUserRequest,
  SystemRole,
  UpdateUserRequest,
  UserResponse,
  UserStatus,
} from "@warmy/generated-api-client";
import { Eye, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { DropdownSelect } from "@/components/ui/dropdown-select";
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
import { TableActionButton } from "@/components/ui/table-actions";
import { TruncatedText } from "@/components/ui/truncated-text";

import { UserDrawer } from "./user-drawer";
import { CreateUserDialog } from "./user-dialog";

type UserManagementProps = {
  currentUser?: UserResponse;
  error?: "permission" | "service";
  loading?: boolean;
  nextCursor?: string | null;
  onCreate?: (payload: CreateUserRequest) => Promise<unknown>;
  onDelete?: (userId: string) => Promise<unknown>;
  onEdit?: (userId: string, payload: UpdateUserRequest) => Promise<unknown>;
  onLoadMore?: () => Promise<unknown>;
  onResetPassword?: (userId: string, password: string) => Promise<unknown>;
  onToggleStatus?: (userId: string, enabled: boolean) => Promise<unknown>;
  paging?: boolean;
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
  onCreate = async () => undefined,
  onDelete = async () => undefined,
  onEdit = async () => undefined,
  onLoadMore = async () => undefined,
  onResetPassword = async () => undefined,
  onToggleStatus = async () => undefined,
  paging = false,
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
  if (!currentUser) {
    return (
      <StatusPanel
        description="当前用户信息不可用，请重新登录后再试。"
        title="无法加载用户管理"
      />
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">用户管理</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            管理内部账号、系统角色和登录状态。
          </p>
        </div>
        <CreateUserDialog onCreate={onCreate} />
      </header>

      <section className="grid grid-cols-4 border-b border-[var(--hairline)] py-4 text-sm max-[900px]:grid-cols-2 max-[900px]:gap-4">
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

      <div
        className="flex items-center gap-3 py-4 max-[760px]:flex-col max-[760px]:items-stretch"
        data-testid="user-filter-bar"
      >
        <label className="relative min-w-0 flex-1 max-[760px]:w-full">
          <Search
            aria-hidden="true"
            className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]"
          />
          <Input
            className="pl-9"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索姓名或邮箱"
            value={query}
          />
        </label>
        <DropdownSelect
          aria-label="按角色筛选"
          className="h-9 basis-40 shrink-0 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 text-sm max-[760px]:basis-auto"
          onChange={(event) =>
            setRole(event.target.value as SystemRole | "all")
          }
          value={role}
        >
          <option value="all">全部角色</option>
          {Object.entries(roleLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </DropdownSelect>
        <DropdownSelect
          aria-label="按状态筛选"
          className="h-9 basis-40 shrink-0 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 text-sm max-[760px]:basis-auto"
          onChange={(event) =>
            setStatus(event.target.value as UserStatus | "all")
          }
          value={status}
        >
          <option value="all">全部状态</option>
          <option value="active">活跃</option>
          <option value="disabled">已禁用</option>
        </DropdownSelect>
      </div>

      <section className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
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
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead>用户</TableHead>
                <TableHead>系统角色</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>登录策略</TableHead>
                <TableHead className="w-20">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.map((user) => (
                <TableRow
                  className="hover:bg-[var(--canvas-soft)]"
                  key={user.id}
                >
                  <TableCell>
                    <TruncatedText className="font-medium">
                      {user.display_name}
                    </TruncatedText>
                    <TruncatedText className="mt-0.5 text-xs text-[var(--muted)]">
                      {user.email}
                    </TruncatedText>
                  </TableCell>
                  <TableCell>
                    <Badge
                      tone={user.role === "super_admin" ? "accent" : "neutral"}
                    >
                      {roleLabels[user.role]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      tone={user.status === "active" ? "success" : "danger"}
                    >
                      {statusLabels[user.status]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {user.must_change_password ? (
                      <Badge tone="warning">需改密</Badge>
                    ) : (
                      <span className="text-[var(--muted)]">正常</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <TableActionButton
                      label={`查看${user.display_name}`}
                      onClick={() => setSelectedUser(user)}
                    >
                      <Eye aria-hidden="true" />
                    </TableActionButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
        {nextCursor ? (
          <div className="flex items-center justify-between gap-3 border-t border-[var(--hairline)] px-4 py-3 text-xs text-[var(--muted)]">
            <span>还有更多用户未显示。</span>
            <button
              className="rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 py-1.5 text-sm font-medium text-[var(--ink)] hover:bg-[var(--canvas-soft)] disabled:cursor-not-allowed disabled:opacity-50"
              disabled={paging}
              onClick={() => void onLoadMore()}
              type="button"
            >
              {paging ? "加载中..." : "加载更多"}
            </button>
          </div>
        ) : null}
      </section>

      <UserDrawer
        currentUser={currentUser}
        onDelete={onDelete}
        onEdit={onEdit}
        onOpenChange={(open) => {
          if (!open) setSelectedUser(undefined);
        }}
        onResetPassword={onResetPassword}
        onToggleStatus={onToggleStatus}
        open={Boolean(selectedUser)}
        user={selectedUser}
      />
    </div>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div className="border-r border-[var(--hairline)] px-4 first:pl-0 last:border-r-0">
      <p className="text-xs text-[var(--muted)]">{label}</p>
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
          <p className="mt-2 text-sm text-[var(--muted)]">{description}</p>
        ) : null}
      </div>
    </div>
  );
}
