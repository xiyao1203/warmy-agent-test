"use client";

import { MessageSquare, Send } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function FeedbackPage() {
  const [type, setType] = useState<"bug" | "feature" | "other">("feature");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // 这里可以添加实际的提交逻辑
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="mx-auto max-w-[600px] px-6 py-16 text-center">
        <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-[var(--success-subtle)]">
          <MessageSquare className="size-8 text-[var(--success)]" />
        </div>
        <h1 className="text-2xl font-semibold">感谢您的反馈！</h1>
        <p className="mt-2 text-[var(--text-muted)]">
          我们会认真处理您的建议，并在后续版本中改进。
        </p>
        <Button
          className="mt-6"
          onClick={() => {
            setSubmitted(false);
            setTitle("");
            setContent("");
          }}
          variant="primary"
        >
          继续反馈
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[600px] px-6 py-8">
      <header className="mb-8">
        <div className="flex items-center gap-3">
          <MessageSquare className="size-8 text-[var(--accent)]" />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">反馈建议</h1>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              帮助我们改进产品，您的反馈对我们非常重要
            </p>
          </div>
        </div>
      </header>

      <form onSubmit={handleSubmit}>
        <div className="space-y-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6">
          <div>
            <label className="mb-2 block text-sm font-medium">反馈类型</label>
            <div className="flex gap-3">
              {[
                { label: "功能建议", value: "feature" as const },
                { label: "问题反馈", value: "bug" as const },
                { label: "其他", value: "other" as const },
              ].map((option) => (
                <button
                  className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                    type === option.value
                      ? "bg-[var(--accent)] text-white"
                      : "bg-[var(--surface-subtle)] text-[var(--text-muted)] hover:bg-[var(--border)]"
                  }`}
                  key={option.value}
                  onClick={() => setType(option.value)}
                  type="button"
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="title">
              标题
            </label>
            <Input
              id="title"
              onChange={(e) => setTitle(e.target.value)}
              placeholder="简要描述您的反馈"
              required
              value={title}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="content">
              详细描述
            </label>
            <textarea
              className="h-32 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm outline-none placeholder:text-[var(--text-subtle)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
              id="content"
              onChange={(e) => setContent(e.target.value)}
              placeholder="请详细描述您的建议或遇到的问题..."
              required
              value={content}
            />
          </div>

          <div className="flex justify-end">
            <Button
              disabled={!title.trim() || !content.trim()}
              type="submit"
              variant="primary"
            >
              <Send className="mr-1.5 size-4" />
              提交反馈
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
