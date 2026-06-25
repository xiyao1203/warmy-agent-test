"use client";

import type { CreateUserRequest, SystemRole } from "@warmy/generated-api-client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

const schema = z.object({
  display_name: z.string().trim().min(1, "请输入姓名"),
  email: z.email("请输入有效的邮箱地址"),
  initial_password: z.string().min(12, "初始密码至少需要 12 个字符"),
  role: z.enum(["super_admin", "developer", "tester", "reviewer", "viewer"]),
});

export function CreateUserDialog({
  onCreate,
}: {
  onCreate: (payload: CreateUserRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [formError, setFormError] = useState("");
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
    setError,
  } = useForm<CreateUserRequest>({
    defaultValues: { display_name: "", email: "", initial_password: "", role: "developer" },
  });

  async function submit(values: CreateUserRequest) {
    setFormError("");
    const result = schema.safeParse(values);
    if (!result.success) {
      for (const issue of result.error.issues) {
        const field = issue.path[0] as keyof CreateUserRequest;
        setError(field, { message: issue.message });
      }
      return;
    }

    try {
      await onCreate(result.data);
      reset();
      setOpen(false);
    } catch {
      setFormError("创建用户失败，请检查输入后重试。");
    }
  }

  return (
    <Dialog
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen);
        if (nextOpen) setFormError("");
      }}
      open={open}
    >
      <DialogTrigger asChild>
        <Button variant="primary">创建用户</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建用户</DialogTitle>
        <DialogDescription>
          用户创建后可以登录，但仍需分配项目成员关系。
        </DialogDescription>
        <form className="mt-5 space-y-4" onSubmit={handleSubmit(submit)}>
          {formError ? (
            <p className="rounded-[var(--radius-sm)] bg-[var(--danger-subtle)] px-3 py-2 text-sm text-[var(--danger)]" role="alert">
              {formError}
            </p>
          ) : null}
          <Field error={errors.display_name?.message} label="姓名">
            <Input autoFocus id="create-display-name" {...register("display_name")} />
          </Field>
          <Field error={errors.email?.message} label="邮箱">
            <Input id="create-email" type="email" {...register("email")} />
          </Field>
          <Field error={errors.initial_password?.message} label="初始密码">
            <Input
              autoComplete="new-password"
              id="create-initial-password"
              type="password"
              {...register("initial_password")}
            />
          </Field>
          <Field error={errors.role?.message} label="系统角色">
            <select
              className="h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 text-sm"
              id="create-role"
              {...register("role")}
            >
              {(
                [
                  ["developer", "开发"],
                  ["tester", "测试"],
                  ["reviewer", "审核"],
                  ["viewer", "只读"],
                  ["super_admin", "超级管理员"],
                ] as Array<[SystemRole, string]>
              ).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </Field>
          <div className="flex justify-end gap-2 pt-2">
            <Button onClick={() => setOpen(false)} type="button">
              取消
            </Button>
            <Button disabled={isSubmitting} type="submit" variant="primary">
              {isSubmitting ? "正在保存…" : "保存用户"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  children,
  error,
  label,
}: {
  children: React.ReactNode;
  error?: string;
  label: string;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium" htmlFor={
        label === "姓名"
          ? "create-display-name"
          : label === "邮箱"
            ? "create-email"
            : label === "初始密码"
              ? "create-initial-password"
              : "create-role"
      }>
        {label}
      </label>
      {children}
      {error ? <p className="mt-1 text-xs text-[var(--danger)]">{error}</p> : null}
    </div>
  );
}
