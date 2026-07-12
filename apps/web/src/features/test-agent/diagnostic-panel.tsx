import type { TrustLoopResultData } from "./mission-types";

export function DiagnosticPanel({
  diagnostics,
}: {
  diagnostics: TrustLoopResultData["diagnostics"];
}) {
  if (!diagnostics.length) return null;
  return (
    <section className="mt-3">
      <h4 className="text-xs font-medium text-[var(--ink)]">证据诊断</h4>
      {diagnostics.map((item) => (
        <p
          className="mt-1 text-xs text-[var(--ink-secondary)]"
          key={item.summary}
        >
          {item.summary} · 置信度 {Math.round(item.confidence * 100)}%
        </p>
      ))}
    </section>
  );
}
