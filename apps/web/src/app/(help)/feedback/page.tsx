import { MessageSquare } from "lucide-react";

import { FeedbackForm } from "@/features/help";

export default function FeedbackPage() {
  return (
    <div className="max-w-2xl space-y-8">
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">
          帮助中心 / 支持
        </p>
        <div className="mt-2 flex items-start gap-3">
          <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] text-[var(--muted)]">
            <MessageSquare className="size-4" />
          </span>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              反馈与建议
            </h1>
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
              报告问题时请说明发生场景、预期结果和实际表现，帮助我们更快定位。
            </p>
          </div>
        </div>
      </header>

      <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-5 sm:p-6">
        <FeedbackForm />
      </div>
    </div>
  );
}
