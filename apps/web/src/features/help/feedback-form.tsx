"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, CheckCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { submitFeedback } from "./api";

const feedbackTypes = [
  { id: "bug", label: "Bug 反馈" },
  { id: "feature", label: "功能建议" },
  { id: "ux", label: "体验优化" },
  { id: "other", label: "其他" },
] as const;

export function FeedbackForm() {
  const [type, setType] = useState<string>("bug");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [contact, setContact] = useState("");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: submitFeedback,
    onSuccess: () => {
      setTitle("");
      setDescription("");
      setContact("");
      setError("");
    },
    onError: () => {
      setError("提交失败，请稍后重试。");
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    if (!title.trim() || !description.trim()) {
      setError("请填写标题和描述");
      return;
    }

    mutation.mutate({
      type: type as "bug" | "feature" | "ux" | "other",
      title: title.trim(),
      description: description.trim(),
      contact: contact.trim() || undefined,
    });
  }

  if (mutation.isSuccess) {
    return (
      <div className="rounded-lg border border-[var(--success)] bg-[var(--success-subtle)] p-8 text-center">
        <CheckCircle className="mx-auto size-8 text-[var(--success)]" />
        <h3 className="mt-3 text-lg font-medium">感谢您的反馈！</h3>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          我们会认真处理您的反馈，并持续改进产品。
        </p>
        <Button
          className="mt-4"
          onClick={() => mutation.reset()}
          variant="secondary"
        >
          继续反馈
        </Button>
      </div>
    );
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div>
        <label className="mb-1.5 block text-sm font-medium">反馈类型</label>
        <div className="flex flex-wrap gap-2">
          {feedbackTypes.map(({ id, label }) => (
            <button
              key={id}
              className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
                type === id
                  ? "bg-[var(--primary)] text-[var(--primary-fg)]"
                  : "bg-[var(--muted)] text-[var(--text-muted)] hover:bg-[var(--accent-subtle)]"
              }`}
              onClick={() => setType(id)}
              type="button"
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium" htmlFor="title">
          标题
        </label>
        <Input
          id="title"
          onChange={(e) => setTitle(e.target.value)}
          placeholder="简要描述您的反馈"
          value={title}
        />
      </div>

      <div>
        <label
          className="mb-1.5 block text-sm font-medium"
          htmlFor="description"
        >
          详细描述
        </label>
        <textarea
          className="h-32 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 text-sm outline-none placeholder:text-[var(--text-subtle)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
          id="description"
          onChange={(e) => setDescription(e.target.value)}
          placeholder="请详细描述您遇到的问题或建议..."
          value={description}
        />
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium" htmlFor="contact">
          联系方式（可选）
        </label>
        <Input
          id="contact"
          onChange={(e) => setContact(e.target.value)}
          placeholder="您的邮箱或其他联系方式"
          value={contact}
        />
      </div>

      {error && (
        <div
          className="rounded-md bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          {error}
        </div>
      )}

      <Button
        className="gap-2"
        disabled={mutation.isPending}
        type="submit"
      >
        <Send className="size-4" />
        {mutation.isPending ? "提交中..." : mutation.isError ? "重新提交" : "提交反馈"}
      </Button>
    </form>
  );
}
