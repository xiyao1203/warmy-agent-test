import Link from "next/link";

import type { TrustLoopResultData } from "./mission-types";

const TITLES = {
  execution: "执行",
  assertion: "断言",
  quality: "质量",
  security: "安全",
} as const;

const STATUS = {
  not_evaluated: "未评估",
  passed: "通过",
  failed: "阻断",
  error: "错误",
  needs_review: "待复核",
} as const;

export function OutcomeGrid({
  outcomes,
  projectId,
}: {
  outcomes: TrustLoopResultData["outcomes"];
  projectId: string;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
      {Object.entries(outcomes).map(([key, outcome]) => (
        <section
          className="rounded-lg border border-[var(--hairline)] p-2"
          key={key}
        >
          <p className="text-xs text-[var(--ink-secondary)]">
            {TITLES[key as keyof typeof TITLES]}
          </p>
          <p className="mt-1 text-sm font-medium text-[var(--ink)]">
            {TITLES[key as keyof typeof TITLES]}
            {STATUS[outcome.status]}
          </p>
          {outcome.evidence_ids[0] ? (
            <Link
              className="mt-1 inline-flex text-xs text-[var(--primary)] hover:underline"
              href={`/projects/${projectId}/runs/evidence/${outcome.evidence_ids[0]}`}
            >
              查看证据
            </Link>
          ) : null}
        </section>
      ))}
    </div>
  );
}
