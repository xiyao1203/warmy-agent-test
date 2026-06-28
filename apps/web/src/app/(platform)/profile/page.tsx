"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Camera,
  Check,
  Copy,
  Key,
  Mail,
  Shield,
  User,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getCurrentUser } from "@/features/auth";

export default function ProfilePage() {
  const userQuery = useQuery({
    queryFn: getCurrentUser,
    queryKey: ["session"],
  });
  const user = userQuery.data;
  const [copied, setCopied] = useState(false);

  if (!user) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <p className="text-sm text-[var(--text-muted)]">加载中...</p>
      </div>
    );
  }

  function copyId() {
    void navigator.clipboard.writeText(user!.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="mx-auto max-w-[800px] px-6 py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">个人资料</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          管理您的个人信息和账号设置
        </p>
      </header>

      {/* 头像区域 */}
      <section className="mb-8 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <div className="flex items-center gap-6">
          <div className="relative">
            <div className="flex size-20 items-center justify-center rounded-full bg-[var(--accent)] text-3xl font-bold text-white">
              {user.display_name.slice(0, 1).toUpperCase()}
            </div>
            <button className="absolute -bottom-1 -right-1 flex size-8 items-center justify-center rounded-full bg-[var(--surface)] text-[var(--text-muted)] shadow-md transition-colors hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]">
              <Camera className="size-4" />
            </button>
          </div>
          <div>
            <h2 className="text-xl font-semibold">{user.display_name}</h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              {user.email}
            </p>
            <div className="mt-2 flex items-center gap-2">
              <Badge tone="accent">{user.role}</Badge>
              <button
                className="flex items-center gap-1 text-xs text-[var(--text-muted)] transition-colors hover:text-[var(--text)]"
                onClick={copyId}
              >
                {copied ? (
                  <>
                    <Check className="size-3" />
                    已复制
                  </>
                ) : (
                  <>
                    <Copy className="size-3" />
                    复制 ID
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 基本信息 */}
      <section className="mb-8 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] px-6 py-4">
          <h3 className="font-semibold">基本信息</h3>
        </div>
        <div className="space-y-4 p-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-[var(--text-muted)]">
                <User className="size-3.5" />
                用户名
              </label>
              <Input disabled value={user.display_name} />
            </div>
            <div>
              <label className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-[var(--text-muted)]">
                <Mail className="size-3.5" />
                邮箱
              </label>
              <Input disabled value={user.email} />
            </div>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--text-muted)]">
              用户 ID
            </label>
            <Input disabled className="font-mono text-xs" value={user.id} />
          </div>
          <div className="flex justify-end">
            <Button variant="primary">编辑资料</Button>
          </div>
        </div>
      </section>

      {/* 安全设置 */}
      <section className="mb-8 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] px-6 py-4">
          <h3 className="font-semibold">安全设置</h3>
        </div>
        <div className="divide-y divide-[var(--border)]">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Key className="size-5 text-[var(--text-muted)]" />
              <div>
                <p className="font-medium">修改密码</p>
                <p className="text-sm text-[var(--text-muted)]">
                  定期修改密码以保护账号安全
                </p>
              </div>
            </div>
            <Button variant="ghost">修改</Button>
          </div>
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Shield className="size-5 text-[var(--text-muted)]" />
              <div>
                <p className="font-medium">两步验证</p>
                <p className="text-sm text-[var(--text-muted)]">
                  启用两步验证以增强账号安全性
                </p>
              </div>
            </div>
            <Badge tone="neutral">未启用</Badge>
          </div>
        </div>
      </section>

      {/* 危险操作 */}
      <section className="rounded-xl border border-[var(--error)] bg-[var(--error-subtle)]">
        <div className="px-6 py-4">
          <h3 className="font-semibold text-[var(--error)]">危险操作</h3>
        </div>
        <div className="border-t border-[var(--error)] px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">删除账号</p>
              <p className="text-sm text-[var(--text-muted)]">
                永久删除您的账号和所有数据，此操作不可恢复
              </p>
            </div>
            <Button variant="danger">删除账号</Button>
          </div>
        </div>
      </section>
    </div>
  );
}
