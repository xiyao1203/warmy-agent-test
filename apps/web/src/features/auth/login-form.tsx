"use client";

import { Eye, EyeOff, LoaderCircle } from "lucide-react";
import { useState, type FormEvent } from "react";
import type { LoginRequest, UserResponse } from "@warmy/generated-api-client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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
      await onLogin(credentials);
      onSuccess(safeReturnTo(returnTo));
    } catch {
      setFormError("邮箱或密码不正确，请重试。");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-4" noValidate onSubmit={handleSubmit}>
      {formError ? (
        <div
          className="rounded-[var(--radius-sm)] border border-[var(--danger)] bg-[var(--danger-subtle)] px-3 py-2 text-sm text-[var(--danger)]"
          role="alert"
        >
          {formError}
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
          onChange={(event) => setEmail(event.target.value)}
          placeholder="name@company.com"
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
            onChange={(event) => setPassword(event.target.value)}
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

      <Button className="w-full" disabled={pending} type="submit" variant="primary">
        {pending ? (
          <>
            <LoaderCircle
              aria-hidden="true"
              className="mr-2 size-4 animate-spin"
            />
            正在登录…
          </>
        ) : (
          "登录"
        )}
      </Button>
    </form>
  );
}
