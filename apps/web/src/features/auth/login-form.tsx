"use client";

import { AlertCircle, Eye, EyeOff } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import type { LoginRequest, UserResponse } from "@warmy/generated-api-client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PulseButton } from "@/components/uiverse";

import { login } from "./api";
import { safeReturnTo } from "./session";

type FieldErrors = Partial<Record<keyof LoginRequest, string>>;

type LoginFormProps = {
  onLogin?: (credentials: LoginRequest) => Promise<UserResponse>;
  onSuccess: (returnTo: string) => void;
  returnTo?: string;
};

function validate(credentials: LoginRequest): FieldErrors {
  const errors: FieldErrors = {};
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(credentials.email.trim())) {
    errors.email = "请输入有效的邮箱地址";
  }
  if (!credentials.password) {
    errors.password = "请输入密码";
  }
  return errors;
}

export function LoginForm({
  onLogin = login,
  onSuccess,
  returnTo,
}: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [pending, setPending] = useState(false);
  const emailRef = useRef<HTMLInputElement>(null);

  // 页面加载时自动聚焦邮箱输入框
  useEffect(() => {
    emailRef.current?.focus();
  }, []);

  /** 输入时清除对应字段错误，提升 UX 即时反馈 */
  function clearFieldError(field: keyof LoginRequest) {
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
    // 同时清除表单级错误
    if (formError) setFormError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    const credentials = { email: email.trim(), password };
    const nextErrors = validate(credentials);
    setErrors(nextErrors);
    setFormError("");
    if (Object.keys(nextErrors).length > 0) return;

    setPending(true);
    try {
      const user = await onLogin(credentials);
      // 如果需要修改密码，跳转到用户管理页（超级管理员视角）
      if (user.must_change_password) {
        onSuccess("/system/users");
        return;
      }
      onSuccess(safeReturnTo(returnTo));
    } catch (err: unknown) {
      // 区分网络错误和凭证错误
      if (err instanceof TypeError && err.message === "Failed to fetch") {
        setFormError("网络连接失败，请检查后端服务是否启动。");
      } else {
        setFormError("邮箱或密码不正确，请重试。");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-4" noValidate onSubmit={handleSubmit}>
      {formError ? (
        <div
          className="flex items-start gap-2 rounded-[var(--radius-sm)] border border-[var(--danger)] bg-[var(--danger-subtle)] px-3.5 py-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          <AlertCircle aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          <span>{formError}</span>
        </div>
      ) : null}

      <div>
        <label className="mb-1.5 block text-sm font-medium" htmlFor="email">
          邮箱
        </label>
        <Input
          aria-describedby={errors.email ? "email-error" : undefined}
          aria-invalid={Boolean(errors.email)}
          autoComplete="email"
          id="email"
          onChange={(event) => {
            setEmail(event.target.value);
            clearFieldError("email");
          }}
          placeholder="name@company.com"
          ref={emailRef}
          type="email"
          value={email}
        />
        {errors.email ? (
          <p className="mt-1 text-xs text-[var(--danger)]" id="email-error">
            {errors.email}
          </p>
        ) : null}
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium" htmlFor="password">
          密码
        </label>
        <div className="relative">
          <Input
            aria-describedby={errors.password ? "password-error" : undefined}
            aria-invalid={Boolean(errors.password)}
            autoComplete="current-password"
            className="pr-10"
            id="password"
            onChange={(event) => {
              setPassword(event.target.value);
              clearFieldError("password");
            }}
            type={showPassword ? "text" : "password"}
            value={password}
          />
          <button
            aria-label={showPassword ? "隐藏密码" : "显示密码"}
            className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-[var(--text-muted)] hover:text-[var(--text)]"
            onClick={() => setShowPassword((value) => !value)}
            type="button"
          >
            {showPassword ? (
              <EyeOff aria-hidden="true" className="size-4" />
            ) : (
              <Eye aria-hidden="true" className="size-4" />
            )}
          </button>
        </div>
        {errors.password ? (
          <p className="mt-1 text-xs text-[var(--danger)]" id="password-error">
            {errors.password}
          </p>
        ) : null}
      </div>

      <PulseButton
        className="mt-2 w-full"
        loading={pending}
        type="submit"
      >
        {pending ? "正在登录…" : "登录"}
      </PulseButton>
    </form>
  );
}
