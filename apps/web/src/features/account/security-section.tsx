"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Lock,
  Shield,
  AlertTriangle,
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
    <div className="space-y-6">
      {/* Password Change */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Lock className="size-5" />
          <h3 className="text-lg font-medium">修改密码</h3>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 rounded-md bg-[var(--success-subtle)] p-3 text-sm text-[var(--success)]">
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
      </div>

      {/* Two-Factor Authentication */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Shield className="size-5" />
          <h3 className="text-lg font-medium">两步验证</h3>
        </div>
        <div className="rounded-md bg-[var(--muted)] p-4">
          <p className="text-sm text-[var(--text-muted)]">
            两步验证功能即将推出，届时您可以通过手机验证码或身份验证器应用增强账户安全性。
          </p>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="rounded-lg border border-[var(--danger)] bg-[var(--card)] p-6">
        <div className="mb-4 flex items-center gap-2">
          <AlertTriangle className="size-5 text-[var(--danger)]" />
          <h3 className="text-lg font-medium text-[var(--danger)]">危险区域</h3>
        </div>
        <p className="mb-4 text-sm text-[var(--text-muted)]">
          删除账户后，所有数据将被永久删除且无法恢复。请谨慎操作。
        </p>
        <Button className="gap-2" variant="danger">
          <AlertTriangle className="size-4" />
          删除账户
        </Button>
      </div>
    </div>
  );
}
