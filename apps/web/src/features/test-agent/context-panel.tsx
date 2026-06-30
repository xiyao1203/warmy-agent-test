import Link from "next/link";

import type { AgentEvent, ArtifactLink } from "./api";

const routeFor = (projectId: string, artifact: ArtifactLink) => {
  const routes: Record<string, string> = {
    agent: "agents",
    dataset: "datasets",
    dataset_version: "datasets",
    test_case: "datasets",
    test_plan: "test-plans",
    test_plan_version: "test-plans",
    run: "runs",
    scorer: "scorers",
    experiment: "experiments",
    security_scan: "security",
    review_task: "reviews",
    release_gate: "gates",
  };
  return `/projects/${projectId}/${routes[artifact.type] ?? "overview"}`;
};

export function ContextPanel({
  artifacts,
  events,
  projectId,
}: {
  artifacts: ArtifactLink[];
  events: AgentEvent[];
  projectId: string;
}) {
  return (
    <aside className="min-h-0 overflow-y-auto border-l border-[var(--border)] bg-[var(--surface)] p-4">
      <h2 className="text-sm font-semibold">关联资产</h2>
      <div className="mt-3 space-y-2">
        {artifacts.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)]">对话产生的平台资产会显示在这里。</p>
        ) : null}
        {artifacts.map((artifact) => (
          <Link
            className="block rounded-[var(--radius-sm)] border border-[var(--border)] p-3 text-sm hover:border-[var(--accent)]"
            href={routeFor(projectId, artifact)}
            key={`${artifact.type}:${artifact.id}:${artifact.relation}`}
          >
            <span className="font-medium">{artifact.type}</span>
            <span className="mt-1 block truncate text-xs text-[var(--text-muted)]">{artifact.id}</span>
          </Link>
        ))}
      </div>
      <h2 className="mt-6 text-sm font-semibold">子 Agent 任务</h2>
      <div className="mt-3 space-y-2">
        {events.filter((event) => event.type.startsWith("agent.")).map((event) => (
          <div className="rounded-[var(--radius-sm)] bg-[var(--surface-subtle)] p-2 text-xs" key={`${event.id}:${event.type}`}>
            {event.type}
          </div>
        ))}
      </div>
    </aside>
  );
}
