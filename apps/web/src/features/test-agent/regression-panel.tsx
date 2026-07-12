import type { TrustLoopResultData } from "./mission-types";

export function RegressionPanel({
  regressions,
}: {
  regressions: TrustLoopResultData["regressions"];
}) {
  if (!regressions.length) return null;
  return (
    <section className="mt-3">
      <h4 className="text-xs font-medium text-[var(--ink)]">回归资产</h4>
      {regressions.map((item) => (
        <p className="mt-1 text-xs text-[var(--ink-secondary)]" key={item.id}>
          {item.state === "quarantined" ? "隔离区" : item.state} ·{" "}
          {item.fingerprint.slice(0, 12)}
        </p>
      ))}
    </section>
  );
}
