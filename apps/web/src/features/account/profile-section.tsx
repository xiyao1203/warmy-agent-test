"use client";

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { UserResponse } from "@warmy/generated-api-client";
import { CheckCircle2, Edit2, Mail, Save, User, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { getCurrentUser, updateProfile } from "./api";

const roleLabels: Record<UserResponse["role"], string> = {
  super_admin: "超级管理员",
  developer: "开发",
  tester: "测试",
  reviewer: "审核者",
  viewer: "只读",
};

const statusLabels: Record<UserResponse["status"], string> = {
  active: "正常",
  disabled: "已禁用",
};

export function ProfileSection() {
  const queryClient = useQueryClient();
  const {
    data: user,
    isError: isUserError,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
  });

  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(["currentUser"], updatedUser);
      setIsEditing(false);
      setError("");
    },
    onError: () => {
      setError("保存失败，请重试");
    },
  });

  function startEditing() {
    if (user) {
      setDisplayName(user.display_name || "");
      setEmail(user.email || "");
    }
    mutation.reset();
    setIsEditing(true);
    setError("");
  }

  function cancelEditing() {
    mutation.reset();
    setIsEditing(false);
    setError("");
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const nextDisplayName = displayName.trim();
    const nextEmail = email.trim();

    if (!nextDisplayName || !nextEmail) {
      setError("请填写显示名称和邮箱地址");
      return;
    }

    setError("");
    mutation.mutate({ display_name: nextDisplayName, email: nextEmail });
  }

  if (isLoading) {
    return (
      <div
        aria-label="正在加载个人资料"
        className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]"
        role="status"
      >
        <div className="animate-pulse space-y-5 p-5">
          <div className="flex items-center gap-4">
            <div className="size-12 rounded-full bg-[var(--surface-subtle)]" />
            <div className="space-y-2">
              <div className="h-4 w-32 rounded bg-[var(--surface-subtle)]" />
              <div className="h-3 w-48 rounded bg-[var(--surface-subtle)]" />
            </div>
          </div>
          <div className="h-28 rounded bg-[var(--surface-subtle)]" />
        </div>
      </div>
    );
  }

  if (isUserError || !user) {
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-6 text-center">
        <p className="text-sm font-medium">无法加载个人资料</p>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          请检查网络连接后重试。
        </p>
        <Button className="mt-4" onClick={() => refetch()} variant="secondary">
          重新加载
        </Button>
      </div>
    );
  }

  const displayLabel = user.display_name || "未设置名称";

  return (
    <div className="space-y-5">
      <section className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 items-center gap-4">
            <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-[var(--accent-subtle)] text-base font-semibold text-[var(--accent)]">
              {(user.display_name?.[0] || user.email[0]).toUpperCase()}
            </div>
            <div className="min-w-0">
              <h2 className="truncate text-lg font-semibold">{displayLabel}</h2>
              <p className="truncate text-sm text-[var(--text-muted)]">
                {user.email}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[var(--border)] bg-[var(--surface-subtle)] px-2.5 py-1 text-xs font-medium text-[var(--text-muted)]">
              {roleLabels[user.role]}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] px-2.5 py-1 text-xs font-medium">
              <CheckCircle2 className="size-3.5 text-[var(--success)]" />
              {statusLabels[user.status]}
            </span>
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="flex items-center justify-between gap-4 border-b border-[var(--border)] px-4 py-3">
          <div>
            <h3 className="text-sm font-semibold">基本资料</h3>
            <p className="mt-0.5 text-xs text-[var(--text-muted)]">
              用于平台内身份展示和账户登录。
            </p>
          </div>
          {!isEditing && (
            <Button
              className="gap-2"
              onClick={startEditing}
              variant="secondary"
            >
              <Edit2 className="size-4" />
              编辑资料
            </Button>
          )}
        </div>

        {isEditing ? (
          <form className="space-y-4 p-4" onSubmit={handleSubmit}>
            {error && (
              <div
                className="rounded-[var(--radius-sm)] bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]"
                role="alert"
              >
                {error}
              </div>
            )}
            <div>
              <label
                className="mb-1.5 block text-sm font-medium"
                htmlFor="display_name"
              >
                显示名称
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--text-muted)]" />
                <Input
                  className="pl-10"
                  disabled={mutation.isPending}
                  id="display_name"
                  onChange={(event) => setDisplayName(event.target.value)}
                  placeholder="输入显示名称"
                  value={displayName}
                />
              </div>
            </div>
            <div>
              <label
                className="mb-1.5 block text-sm font-medium"
                htmlFor="email"
              >
                邮箱地址
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--text-muted)]" />
                <Input
                  className="pl-10"
                  disabled={mutation.isPending}
                  id="email"
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="输入邮箱地址"
                  type="email"
                  value={email}
                />
              </div>
            </div>
            <div className="flex flex-wrap gap-2 pt-1">
              <Button
                className="gap-2"
                disabled={mutation.isPending}
                type="submit"
              >
                <Save className="size-4" />
                {mutation.isPending ? "保存中..." : "保存资料"}
              </Button>
              <Button
                className="gap-2"
                disabled={mutation.isPending}
                onClick={cancelEditing}
                type="button"
                variant="secondary"
              >
                <X className="size-4" />
                取消
              </Button>
            </div>
          </form>
        ) : (
          <dl className="divide-y divide-[var(--border)]">
            <ProfileRow label="显示名称" value={displayLabel} />
            <ProfileRow label="登录邮箱" value={user.email} />
          </dl>
        )}
      </section>

      <section className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] px-4 py-3">
          <h3 className="text-sm font-semibold">账户信息</h3>
          <p className="mt-0.5 text-xs text-[var(--text-muted)]">
            系统分配的身份与访问状态。
          </p>
        </div>
        <dl className="divide-y divide-[var(--border)]">
          <ProfileRow code label="用户 ID" value={user.id} />
          <ProfileRow label="系统角色" value={roleLabels[user.role]} />
          <ProfileRow label="账户状态" value={statusLabels[user.status]} />
        </dl>
      </section>
    </div>
  );
}

function ProfileRow({
  code = false,
  label,
  value,
}: {
  code?: boolean;
  label: string;
  value: string;
}) {
  return (
    <div className="grid gap-1 px-4 py-3 sm:grid-cols-[9rem_minmax(0,1fr)] sm:items-center">
      <dt className="text-sm text-[var(--text-muted)]">{label}</dt>
      <dd
        className={
          code
            ? "break-all font-mono text-xs text-[var(--text)]"
            : "break-words text-sm font-medium"
        }
      >
        {value}
      </dd>
    </div>
  );
}
