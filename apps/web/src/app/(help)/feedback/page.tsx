"use client";

import { ArrowLeft, MessageSquare, Send } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const feedbackTypes = [
  { description: "报告产品缺陷或异常行为", value: "bug" },
  { description: "提出新功能或改进建议", value: "feature" },
  { description: "改善用户体验的建议", value: "ux" },
  { description: "其他类型的反馈", value: "other" },
];

export default function FeedbackPage() {
  const [type, setType] = useState("bug");
  const [submitted, setSubmitted] = useState(false);

  if (submitted) {
    return (
      <div className="min-h-screen bg-[var(--background)]">
        <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-sm">
          <div className="mx-auto flex h-14 max-w-[600px] items-center justify-between px-6">
            <Link
              className="flex items-center gap-2 text-sm font-semibold transition-colors hover:text-[var(--accent)]"
              href="/projects"
            >
              <ArrowLeft className="size-4" />
              返回应用
            </Link>
            <span className="text-sm font-semibold">帮助中心</span>
            <div className="w-20" />
          </div>
        </header>
        <div className="grid min-h-[80vh] place-items-center">
          <div className="text-center">
            <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-[var(--success)] text-3xl text-white">
              ✓
            </div>
            <h1 className="mt-6 text-2xl font-semibold">感谢您的反馈！</h1>
            <p className="mt-2 text-[var(--text-muted)]">
              我们会认真处理您的建议，并持续改进产品。
            </p>
            <Link
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--accent-strong)]"
              href="/projects"
            >
              返回应用
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-[600px] items-center justify-between px-6">
          <Link
            className="flex items-center gap-2 text-sm font-semibold transition-colors hover:text-[var(--accent)]"
            href="/projects"
          >
            <ArrowLeft className="size-4" />
            返回应用
          </Link>
          <span className="text-sm font-semibold">帮助中心</span>
          <div className="w-20" />
        </div>
      </header>

      <div className="mx-auto max-w-[600px] px-6 py-8">
        <header className="mb-8">
          <div className="flex items-center gap-3">
            <MessageSquare className="size-8 text-[var(--accent)]" />
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                反馈建议
              </h1>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                帮助我们改进产品，您的反馈很重要
              </p>
            </div>
          </div>
        </header>

        <form
          className="space-y-6"
          onSubmit={(e) => {
            e.preventDefault();
            setSubmitted(true);
          }}
        >
          {/* 反馈类型 */}
          <div>
            <label className="mb-3 block text-sm font-medium">
              反馈类型
            </label>
            <div className="grid gap-2 sm:grid-cols-2">
              {feedbackTypes.map((item) => (
                <button
                  className={`rounded-lg border px-4 py-3 text-left text-sm transition-all ${
                    type === item.value
                      ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]"
                      : "border-[var(--border)] hover:border-[var(--border-strong)]"
                  }`}
                  key={item.value}
                  onClick={() => setType(item.value)}
                  type="button"
                >
                  <p className="font-medium">
                    {item.value === "bug"
                      ? "Bug 报告"
                      : item.value === "feature"
                        ? "功能建议"
                        : item.value === "ux"
                          ? "体验优化"
                          : "其他"}
                  </p>
                  <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                    {item.description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* 标题 */}
          <div>
            <label className="mb-1.5 block text-sm font-medium">标题</label>
            <input
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm transition-colors focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
              placeholder="简要描述您的反馈"
              required
            />
          </div>

          {/* 详细描述 */}
          <div>
            <label className="mb-1.5 block text-sm font-medium">
              详细描述
            </label>
            <textarea
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm transition-colors focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
              minLength={10}
              placeholder="请详细描述您遇到的问题或建议..."
              required
              rows={5}
            />
          </div>

          {/* 联系方式 */}
          <div>
            <label className="mb-1.5 block text-sm font-medium">
              联系方式（可选）
            </label>
            <input
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm transition-colors focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
              placeholder="邮箱或其他联系方式"
              type="email"
            />
          </div>

          {/* 提交按钮 */}
          <button
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--accent-strong)]"
            type="submit"
          >
            <Send className="size-4" />
            提交反馈
          </button>
        </form>
      </div>
    </div>
  );
}
