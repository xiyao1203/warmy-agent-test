"use client";

import { useState, type FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { User, Mail, Save, X, Edit2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { getCurrentUser, updateProfile } from "./api";

export function ProfileSection() {
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useQuery({
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
    setIsEditing(true);
    setError("");
  }

  function cancelEditing() {
    setIsEditing(false);
    setError("");
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate({ display_name: displayName, email });
  }

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-24 rounded bg-[var(--muted)]" />
          <div className="h-10 w-full rounded bg-[var(--muted)]" />
          <div className="h-10 w-full rounded bg-[var(--muted)]" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <p className="text-[var(--text-muted)]">无法加载用户信息</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="flex items-center gap-4">
          <div className="flex size-16 items-center justify-center rounded-full bg-[var(--primary)] text-2xl font-bold text-[var(--primary-fg)]">
            {user.display_name?.[0] || user.email[0].toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-semibold">{user.display_name || "未设置名称"}</h2>
            <p className="text-sm text-[var(--text-muted)]">{user.email}</p>
          </div>
        </div>
      </div>

      {/* Profile Form */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-medium">基本信息</h3>
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

        {error && (
          <div className="mb-4 rounded-md bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]">
            {error}
          </div>
        )}

        {isEditing ? (
          <form className="space-y-4" onSubmit={handleSubmit}>
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
                  id="display_name"
                  onChange={(e) => setDisplayName(e.target.value)}
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
                  id="email"
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="输入邮箱地址"
                  type="email"
                  value={email}
                />
              </div>
            </div>

            <div className="flex gap-2">
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
          <div className="space-y-4">
            <div className="flex items-center gap-3 rounded-md border border-[var(--border)] p-3">
              <User className="size-5 text-[var(--text-muted)]" />
              <div>
                <p className="text-xs text-[var(--text-muted)]">显示名称</p>
                <p className="font-medium">{user.display_name || "未设置"}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-md border border-[var(--border)] p-3">
              <Mail className="size-5 text-[var(--text-muted)]" />
              <div>
                <p className="text-xs text-[var(--text-muted)]">邮箱地址</p>
                <p className="font-medium">{user.email}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Account Info */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <h3 className="mb-4 text-lg font-medium">账户信息</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--text-muted)]">用户 ID</span>
            <code className="rounded bg-[var(--muted)] px-2 py-1 text-xs">
              {user.id}
            </code>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--text-muted)]">角色</span>
            <span className="text-sm font-medium">{user.role}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
