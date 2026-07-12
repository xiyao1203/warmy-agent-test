import type { TrustLoopResultData } from "./mission-types";

export function GateDecisionCard({
  gate,
}: {
  gate: TrustLoopResultData["gate"];
}) {
  const title =
    gate.status === "allow"
      ? "门禁允许"
      : gate.status === "block"
        ? "门禁阻断"
        : "门禁待复核";
  return (
    <section className="mt-3 rounded-lg border border-[var(--hairline)] p-2">
      <h4 className="text-sm font-medium text-[var(--ink)]">{title}</h4>
      {gate.rules.map((rule) => (
        <p className="mt-1 text-xs text-[var(--ink-secondary)]" key={rule.code}>
          {rule.reason}（阈值 {rule.threshold}，实际 {rule.actual}）
        </p>
      ))}
    </section>
  );
}
