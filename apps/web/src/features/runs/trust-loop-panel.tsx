import type { ReactNode } from "react";
import {
  AlertTriangle,
  CircleDashed,
  FlaskConical,
  GitBranch,
  Search,
  ShieldAlert,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { SkeletonText } from "@/components/uiverse";

import type { RunTrustLoopData } from "./api";

const STAGES = [
  ["classify", "分类"],
  ["diagnose", "诊断"],
  ["reproduce", "复现"],
  ["calibrate", "校准"],
  ["evaluate_gate", "门禁"],
  ["finalize", "完成"],
] as const;

export function TrustLoopPanel({
  compact = false,
  data,
  error,
  loading = false,
  projectId,
  runId,
}: {
  compact?: boolean;
  data?: RunTrustLoopData;
  error?: string;
  loading?: boolean;
  projectId: string;
  runId: string;
}) {
  const frame = compact
    ? "border-t border-[var(--hairline)] pt-3"
    : "rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-5";
  if (loading) {
    return (
      <section aria-label="可信闭环" className={`${frame} min-h-52`}>
        <h2 className="text-base font-semibold">可信闭环</h2>
        <SkeletonText className="mt-4" lines={5} />
      </section>
    );
  }
  if (error || !data) {
    return (
      <section aria-label="可信闭环" className={`${frame} min-h-32`}>
        <h2 className="text-base font-semibold">可信闭环</h2>
        <div className="mt-3 flex items-center gap-2 text-sm text-[var(--danger)]">
          <AlertTriangle aria-hidden="true" className="size-4" />
          {error ?? "可信闭环结果暂不可用"}
        </div>
      </section>
    );
  }

  const status = trustLoopStatus(data.summary.status);
  const currentIndex = STAGES.findIndex(
    ([stage]) => stage === data.summary.current_stage,
  );
  const classifications = data.summary.classifications
    .map(asRecord)
    .filter((item): item is Record<string, unknown> => item !== null);
  const gateRules = data.gate.rules
    .map(asRecord)
    .filter((item): item is Record<string, unknown> => item !== null);
  const decision = data.gate.decision;

  return (
    <section aria-label="可信闭环" className={frame}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">可信闭环</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">
            {data.summary.pipeline_version}
          </p>
        </div>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>

      <ol className="mt-4 grid grid-cols-6 gap-1 max-sm:grid-cols-3">
        {STAGES.map(([stage, label], index) => {
          const reached =
            data.summary.status === "completed" ||
            data.summary.status === "completed_with_warnings" ||
            index <= currentIndex;
          return (
            <li
              className={`min-w-0 border-t-2 pt-2 text-center text-xs ${
                reached
                  ? "border-[var(--primary)] text-[var(--ink)]"
                  : "border-[var(--hairline)] text-[var(--muted)]"
              }`}
              key={stage}
            >
              {label}
            </li>
          );
        })}
      </ol>

      <div className="mt-5 grid grid-cols-2 gap-x-6 gap-y-5 max-md:grid-cols-1">
        <PanelSection
          icon={<Search className="size-4" />}
          title="失败分类与诊断"
        >
          {classifications.length ? (
            <ul className="space-y-2">
              {classifications.map((item, index) => {
                const caseId = text(item.run_case_id);
                return (
                  <li className="text-sm" key={caseId ?? index}>
                    <span className="font-medium">
                      {failureClassLabel(text(item.failure_class))}
                    </span>
                    <span className="ml-2 text-xs text-[var(--muted)]">
                      {text(item.code) ?? "未分类"}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <EmptyText>暂无失败分类</EmptyText>
          )}
          <div className="mt-3 space-y-3 border-t border-[var(--hairline)] pt-3">
            {data.diagnostics.length ? (
              data.diagnostics.map((diagnostic) => (
                <div key={diagnostic.id}>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium">
                      {diagnostic.status === "inconclusive"
                        ? "诊断无结论"
                        : diagnostic.summary || "诊断完成"}
                    </span>
                    <Badge
                      tone={
                        diagnostic.status === "inconclusive"
                          ? "warning"
                          : "neutral"
                      }
                    >
                      {Math.round(diagnostic.confidence * 100)}%
                    </Badge>
                  </div>
                  {diagnostic.verification_steps.length ? (
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      {diagnostic.verification_steps.join("；")}
                    </p>
                  ) : null}
                  {diagnostic.evidence_ids[0] ? (
                    <Link
                      className="mt-1 inline-flex text-xs font-medium text-[var(--primary)] hover:underline"
                      href={evidenceHref(
                        projectId,
                        runId,
                        diagnostic.run_case_id,
                        diagnostic.evidence_ids[0],
                      )}
                    >
                      查看用例证据
                    </Link>
                  ) : null}
                </div>
              ))
            ) : (
              <EmptyText>暂无诊断结论</EmptyText>
            )}
          </div>
        </PanelSection>

        <PanelSection icon={<GitBranch className="size-4" />} title="回归候选">
          {data.regressions.length ? (
            <ul className="space-y-3">
              {data.regressions.map((candidate) => (
                <li key={candidate.id}>
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="font-medium">
                      {candidate.fingerprint.slice(0, 12)}
                    </span>
                    <Badge
                      tone={
                        candidate.status === "quarantined"
                          ? "warning"
                          : "neutral"
                      }
                    >
                      {regressionStatus(candidate.status)}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    独立复现 {candidate.reproduction_count} 次
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyText>暂无回归候选</EmptyText>
          )}
        </PanelSection>

        <PanelSection
          icon={<FlaskConical className="size-4" />}
          title="评估校准"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              tone={
                data.calibration.status === "inconclusive"
                  ? "warning"
                  : "neutral"
              }
            >
              {data.calibration.status === "inconclusive" ? "无结论" : "已计算"}
            </Badge>
            {metric(data.calibration.metrics, "accuracy") !== null ? (
              <span className="text-sm">
                准确率{" "}
                {Math.round(
                  metric(data.calibration.metrics, "accuracy")! * 100,
                )}
                %
              </span>
            ) : (
              <span className="text-sm text-[var(--muted)]">暂无可用样本</span>
            )}
          </div>
        </PanelSection>

        <PanelSection
          icon={<ShieldAlert className="size-4" />}
          title="联合门禁"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={gateTone(decision)}>
              {gateLabel(decision, data.gate.status)}
            </Badge>
          </div>
          {gateRules.length ? (
            <ul className="mt-3 space-y-3">
              {gateRules.map((rule, index) => (
                <li className="text-sm" key={text(rule.code) ?? index}>
                  <p className="font-medium">
                    {text(rule.reason) ?? "门禁规则未通过"}
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    阈值 {text(rule.threshold) ?? "-"}，实际{" "}
                    {text(rule.actual) ?? "-"}
                  </p>
                  {firstString(rule.evidence_refs) ? (
                    <Link
                      className="mt-1 inline-flex text-xs font-medium text-[var(--primary)] hover:underline"
                      href={evidenceHref(
                        projectId,
                        runId,
                        firstCaseId(data) ?? "all",
                        firstString(rule.evidence_refs)!,
                      )}
                    >
                      查看门禁证据
                    </Link>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyText>暂无阻断规则</EmptyText>
          )}
        </PanelSection>
      </div>

      {data.summary.warning_codes.length ? (
        <div className="mt-5 flex items-start gap-2 border-t border-[var(--hairline)] pt-3 text-xs text-[var(--warning)]">
          <AlertTriangle
            aria-hidden="true"
            className="mt-0.5 size-4 shrink-0"
          />
          <span>{data.summary.warning_codes.map(warningLabel).join("；")}</span>
        </div>
      ) : null}
    </section>
  );
}

function PanelSection({
  children,
  icon,
  title,
}: {
  children: ReactNode;
  icon: ReactNode;
  title: string;
}) {
  return (
    <section className="min-w-0 border-t border-[var(--hairline)] pt-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold">
        {icon}
        {title}
      </h3>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function EmptyText({ children }: { children: ReactNode }) {
  return (
    <p className="flex items-center gap-2 text-sm text-[var(--muted)]">
      <CircleDashed aria-hidden="true" className="size-4" />
      {children}
    </p>
  );
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.length ? value : null;
}

function firstString(value: unknown): string | null {
  return Array.isArray(value) ? text(value[0]) : null;
}

function metric(values: Record<string, unknown>, key: string): number | null {
  return typeof values[key] === "number" ? values[key] : null;
}

function firstCaseId(data: RunTrustLoopData): string | null {
  return (
    data.diagnostics[0]?.run_case_id ?? data.regressions[0]?.run_case_id ?? null
  );
}

function evidenceHref(
  projectId: string,
  runId: string,
  caseId: string,
  evidenceId: string,
) {
  return `/projects/${projectId}/runs/${runId}?case=${encodeURIComponent(caseId)}&evidence=${encodeURIComponent(evidenceId)}`;
}

function trustLoopStatus(status: string): {
  label: string;
  tone: "neutral" | "accent" | "success" | "warning" | "danger";
} {
  if (status === "pending") return { label: "后处理排队中", tone: "neutral" };
  if (status === "running") return { label: "后处理中", tone: "accent" };
  if (status === "completed") return { label: "完成", tone: "success" };
  if (status === "completed_with_warnings") {
    return { label: "完成（有警告）", tone: "warning" };
  }
  return { label: "后处理失败", tone: "danger" };
}

function failureClassLabel(value: string | null) {
  const labels: Record<string, string> = {
    assertion_failure: "断言失败",
    infrastructure_failure: "基础设施失败",
    target_failure: "目标失败",
    test_failure: "测试缺陷",
  };
  return value ? (labels[value] ?? value) : "未分类";
}

function regressionStatus(status: string) {
  if (status === "quarantined") return "隔离";
  if (status === "published") return "已发布";
  if (status === "verified") return "已验证";
  return status;
}

function gateLabel(decision: string | null, status: string) {
  if (status === "pending") return "门禁待计算";
  if (decision === "allow") return "门禁允许";
  if (decision === "block") return "门禁阻断";
  if (decision === "quarantine") return "门禁隔离";
  return "门禁待复核";
}

function gateTone(
  decision: string | null,
): "success" | "danger" | "warning" | "neutral" {
  if (decision === "allow") return "success";
  if (decision === "block") return "danger";
  if (decision === "quarantine") return "warning";
  return "neutral";
}

function warningLabel(code: string) {
  const labels: Record<string, string> = {
    diagnostic_model_unavailable: "诊断模型不可用，结果标记为无结论",
    diagnosis_inconclusive: "诊断证据不足",
    insufficient_calibration_samples: "校准样本不足",
    reproducer_unavailable: "复现执行器不可用",
  };
  return labels[code] ?? code;
}
