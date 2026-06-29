"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Lock,
  Shield,
  Eye,
  EyeOff,
  Save,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { changePassword } from "./api";

export function SecuritySection() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const mutation = useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setError("");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    },
    onError: () => {
      setError("密码修改失败，请检查当前密码是否正确");
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess(false);

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("请填写所有密码字段");
      return;
    }

    if (newPassword.length < 8) {
      setError("新密码长度至少为 8 个字符");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("两次输入的新密码不一致");
      return;
    }

    mutation.mutate({
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  return (
    <div className="space-y-5">
      <section className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 sm:p-5">
        <div className="mb-4 flex items-start gap-3 border-b border-[var(--border)] pb-4">
          <Lock className="mt-0.5 size-4 text-[var(--text-muted)]" />
          <div>
            <h3 className="text-sm font-semibold">修改密码</h3>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              使用当前密码验证身份后设置新密码。
            </p>
          </div>
        </div>

        {error && (
          <div
            className="mb-4 rounded-md bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]"
            role="alert"
          >
            {error}
          </div>
        )}

        {success && (
          <div
            className="mb-4 rounded-md bg-[var(--success-subtle)] p-3 text-sm text-[var(--success)]"
            role="status"
          >
            密码修改成功
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label
              className="mb-1.5 block text-sm font-medium"
              htmlFor="current_password"
            >
              当前密码
            </label>
            <div className="relative">
              <Input
                className="pr-10"
                id="current_password"
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="输入当前密码"
                type={showCurrentPassword ? "text" : "password"}
                value={currentPassword}
              />
              <button
                aria-label={showCurrentPassword ? "隐藏密码" : "显示密码"}
                className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-[var(--text-muted)]"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                type="button"
              >
                {showCurrentPassword ? (
                  <EyeOff className="size-4" />
                ) : (
                  <Eye className="size-4" />
                )}
              </button>
            </div>
          </div>

          <div>
            <label
              className="mb-1.5 block text-sm font-medium"
              htmlFor="new_password"
            >
              新密码
            </label>
            <div className="relative">
              <Input
                className="pr-10"
                id="new_password"
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="输入新密码（至少 8 个字符）"
                type={showNewPassword ? "text" : "password"}
                value={newPassword}
              />
              <button
                aria-label={showNewPassword ? "隐藏密码" : "显示密码"}
                className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-[var(--text-muted)]"
                onClick={() => setShowNewPassword(!showNewPassword)}
                type="button"
              >
                {showNewPassword ? (
                  <EyeOff className="size-4" />
                ) : (
                  <Eye className="size-4" />
                )}
              </button>
            </div>
          </div>

          <div>
            <label
              className="mb-1.5 block text-sm font-medium"
              htmlFor="confirm_password"
            >
              确认新密码
            </label>
            <Input
              id="confirm_password"
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="再次输入新密码"
              type="password"
              value={confirmPassword}
            />
          </div>

          <Button
            className="gap-2"
            disabled={mutation.isPending}
            type="submit"
          >
            <Save className="size-4" />
            {mutation.isPending ? "修改中..." : "修改密码"}
          </Button>
        </form>
      </section>

      <section className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 sm:p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Shield className="mt-0.5 size-4 text-[var(--text-muted)]" />
            <div>
              <h3 className="text-sm font-semibold">两步验证</h3>
              <p className="mt-1 text-xs leading-5 text-[var(--text-muted)]">
                当前账户暂不支持手机验证码或身份验证器绑定。
              </p>
            </div>
          </div>
          <span className="shrink-0 rounded-full bg-[var(--surface-subtle)] px-2.5 py-1 text-xs font-medium text-[var(--text-muted)]">
            暂未开放
          </span>
        </div>
      </section>
    </div>
  );
}
