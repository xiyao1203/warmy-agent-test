import Link from "next/link";

import type { AgentRelationships } from "./api";

export function RunsTab({
  items,
  projectId,
}: {
  items: AgentRelationships["runs"];
  projectId: string;
}) {
  return (
    <RelationshipList
      empty="暂无关联运行。请先在测试计划中选择已发布版本并执行。"
      items={items.map((item) => ({
        id: item.id,
        label: `运行 ${item.id.slice(0, 8)} · ${item.status} · ${item.passed_cases}/${item.total_cases}`,
        href: `/projects/${projectId}/runs/${item.id}`,
      }))}
    />
  );
}

export function ArtifactsTab({
  items,
  projectId,
}: {
  items: AgentRelationships["artifacts"];
  projectId: string;
}) {
  return (
    <RelationshipList
      empty="暂无关联产物。"
      items={items.map((item) => ({
        id: item.id,
        label: item.filename,
        href: `/projects/${projectId}/runs/${item.run_id}`,
      }))}
    />
  );
}

export function RelationshipList({
  items,
  empty,
}: {
  items: Array<{ id: string; label: string; href: string }>;
  empty: string;
}) {
  if (!items.length)
    return <p className="text-sm text-[var(--muted)]">{empty}</p>;
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <Link
          className="block rounded-lg border border-[var(--hairline)] px-4 py-3 text-sm hover:bg-[var(--canvas-soft)]"
          href={item.href}
          key={item.id}
        >
          {item.label}
        </Link>
      ))}
    </div>
  );
}

export function RelationshipsTab({
  relationships,
  projectId,
}: {
  relationships?: AgentRelationships;
  projectId: string;
}) {
  if (!relationships)
    return <p className="text-sm text-[var(--muted)]">正在加载关联资产…</p>;
  const groups = [
    [
      "测试计划",
      relationships.plans.map((item) => ({
        id: item.id,
        label: `${item.name} v${item.version_number} · ${item.status}`,
        href: `/projects/${projectId}/test-plans/${item.plan_id}`,
      })),
    ],
    [
      "实验",
      relationships.experiments.map((item) => ({
        id: item.id,
        label: `${item.name} · ${item.status}`,
        href: `/projects/${projectId}/experiments`,
      })),
    ],
    [
      "安全扫描",
      relationships.security_scans.map((item) => ({
        id: item.id,
        label: `${item.scan_type} · ${item.status}`,
        href: `/projects/${projectId}/security`,
      })),
    ],
    [
      "发布门禁",
      relationships.gates.map((item) => ({
        id: item.id,
        label: `${item.name} · ${item.status}`,
        href: `/projects/${projectId}/gates`,
      })),
    ],
  ] as const;
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      {groups.map(([title, items]) => (
        <section key={title}>
          <h2 className="mb-2 text-sm font-semibold">{title}</h2>
          <RelationshipList empty={`暂无${title}关联。`} items={[...items]} />
        </section>
      ))}
    </div>
  );
}
