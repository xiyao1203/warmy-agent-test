import { CheckCircle2, CircleAlert, Loader2 } from "lucide-react";
import Link from "next/link";

import type { MissionProgressOutput } from "./mission-types";

export function MissionProgressCard({
  output,
  projectId,
}: {
  output: MissionProgressOutput;
  projectId: string;
}) {
  const terminal = ["completed", "failed", "cancelled"].includes(output.status);
  const failed = output.status === "failed";
  const Icon = failed ? CircleAlert : terminal ? CheckCircle2 : Loader2;
  const label = failed
    ? "全链路测试需要处理"
    : terminal
      ? "全链路测试已完成"
      : "全链路测试执行中";
  return (
    <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface)] p-3">
      <div className="flex items-center gap-2">
        <Icon
          className={`size-4 ${failed ? "text-[var(--danger)]" : "text-[var(--primary)]"} ${terminal ? "" : "animate-spin"}`}
        />
        <span className="text-sm font-medium text-[var(--ink)]">{label}</span>
      </div>
      {output.missing_fields?.length ? (
        <p className="mt-2 text-xs text-[var(--warning)]">
          还需提供：{output.missing_fields.join("、")}
        </p>
      ) : null}
      {output.run_id ? (
        <Link
          className="mt-2 inline-flex text-xs font-medium text-[var(--primary)] hover:underline"
          href={`/projects/${projectId}/runs/${output.run_id}`}
        >
          查看运行详情
        </Link>
      ) : null}
    </div>
  );
}
