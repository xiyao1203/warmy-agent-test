import {
  Bot,
  ClipboardCheck,
  Database,
  FlaskConical,
  KeyRound,
  MessageSquareText,
  PlayCircle,
  Scale,
  Shield,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

import type { AgentEvent, ArtifactLink } from "./api";

const typeMeta: Record<
  string,
  {
    label: string;
    icon: typeof Bot;
    route: string;
  }
> = {
  agent: { label: "智能体", icon: Bot, route: "agents" },
  dataset: { label: "测试集", icon: Database, route: "datasets" },
  dataset_version: { label: "数据集版本", icon: Database, route: "datasets" },
  test_case: { label: "测试用例", icon: ClipboardCheck, route: "datasets" },
  test_plan: { label: "测试计划", icon: ClipboardCheck, route: "test-plans" },
  test_plan_version: {
    label: "计划版本",
    icon: ClipboardCheck,
    route: "test-plans",
  },
  run: { label: "运行记录", icon: PlayCircle, route: "runs" },
  scorer: { label: "评分器", icon: Scale, route: "scorers" },
  experiment: { label: "实验对比", icon: FlaskConical, route: "experiments" },
  security_scan: { label: "安全扫描", icon: Shield, route: "security" },
  review_task: { label: "审核任务", icon: MessageSquareText, route: "reviews" },
  release_gate: { label: "发布门禁", icon: ShieldCheck, route: "gates" },
  environment_template: {
    label: "环境模板",
    icon: KeyRound,
    route: "environments",
  },
};

const agentEventLabel: Record<string, string> = {
  "agent.delegated": "已委派",
  "agent.progress": "执行中",
  "agent.completed": "已完成",
};

function artifactHref(projectId: string, artifact: ArtifactLink) {
  const meta = typeMeta[artifact.type];
  return `/projects/${projectId}/${meta?.route ?? "overview"}`;
}

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
    <aside className="flex min-h-0 flex-col overflow-y-auto border-l border-[var(--hairline)] bg-[var(--surface)]">
      <div className="p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.66px] text-[var(--muted)]">
          关联资产
        </h3>
        {artifacts.length === 0 ? (
          <p className="mt-2 text-xs text-[var(--muted)]">
            对话产生的平台资产会
            <br />
            显示在这里。
          </p>
        ) : (
          <div className="mt-2 space-y-1.5">
            {artifacts.map((artifact) => {
              const meta = typeMeta[artifact.type] ?? {
                label: artifact.type,
                icon: Sparkles,
              };
              const Icon = meta.icon;
              return (
                <Link
                  className="flex items-center gap-2.5 rounded-[var(--radius-md)] p-2 text-sm transition-colors hover:bg-[var(--canvas-soft)]"
                  href={artifactHref(projectId, artifact)}
                  key={`${artifact.type}:${artifact.id}:${artifact.relation}`}
                >
                  <span className="flex size-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-[var(--canvas-soft)] text-[var(--muted)]">
                    <Icon aria-hidden="true" className="size-3.5" />
                  </span>
                  <span className="min-w-0 truncate text-[var(--ink)]">
                    {meta.label}
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      <div className="border-t border-[var(--hairline)] p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.66px] text-[var(--muted)]">
          子 Agent 任务
        </h3>
        {events.filter((e) => e.type.startsWith("agent.")).length === 0 ? (
          <p className="mt-2 text-xs text-[var(--muted)]">
            暂无子 Agent 任务。
          </p>
        ) : (
          <div className="mt-2 space-y-1">
            {events
              .filter((e) => e.type.startsWith("agent."))
              .map((event) => {
                const label =
                  agentEventLabel[event.type] ??
                  event.type.replace("agent.", "");
                return (
                  <div
                    className="flex items-center gap-2.5 rounded-[var(--radius-md)] p-2 text-sm text-[var(--ink)]"
                    key={`${event.id}:${event.type}`}
                  >
                    <span className="flex size-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-[var(--canvas-soft)] text-[var(--primary)]">
                      <Bot aria-hidden="true" className="size-3.5" />
                    </span>
                    <span className="min-w-0 truncate">{label}</span>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </aside>
  );
}
