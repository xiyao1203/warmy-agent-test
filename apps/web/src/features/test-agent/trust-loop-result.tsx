import { DiagnosticPanel } from "./diagnostic-panel";
import { GateDecisionCard } from "./gate-decision-card";
import type { TrustLoopResultData } from "./mission-types";
import { OutcomeGrid } from "./outcome-grid";
import { RegressionPanel } from "./regression-panel";

export function TrustLoopResult({
  result,
  projectId,
}: {
  result: TrustLoopResultData;
  projectId: string;
}) {
  return (
    <section className="mt-3 border-t border-[var(--hairline)] pt-3">
      <OutcomeGrid outcomes={result.outcomes} projectId={projectId} />
      <DiagnosticPanel diagnostics={result.diagnostics} />
      <RegressionPanel regressions={result.regressions} />
      <GateDecisionCard gate={result.gate} />
    </section>
  );
}
