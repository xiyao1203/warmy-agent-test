import { ArrowLeft, MessageSquare } from "lucide-react";
import Link from "next/link";

import { FeedbackForm } from "@/features/help";

export default function FeedbackPage() {
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

        <FeedbackForm />
      </div>
    </div>
  );
}
