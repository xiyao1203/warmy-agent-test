import {
  Bot,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FlaskConical,
  KeyRound,
  Loader2,
  MessageSquareText,
  PlayCircle,
  Scale,
  Shield,
  ShieldCheck,
  Sparkles,
  XCircle,
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

const agentIcons: Record<string, typeof Bot> = {
  target_agent: Bot,
  test_data: Database,
  test_plan: ClipboardCheck,
  execution: PlayCircle,
  evaluation: Scale,
  security: Shield,
  review_gate: ShieldCheck,
  experiment: FlaskConical,
  environment: Shield,
};

function artifactHref(projectId: string, artifact: ArtifactLink) {
  const meta = typeMeta[artifact.type];
  return `/projects/${projectId}/${meta?.route ?? "overview"}`;
}

type TaskSummary = {
  taskId: string;
  childAgent: string;
  capability: string;
  status: "delegated" | "running" | "completed" | "failed";
};

function groupTasks(events: AgentEvent[]): TaskSummary[] {
  const groups = new Map<
    string,
    { delegated: AgentEvent | null; latest: AgentEvent }
  >();
  const order: string[] = [];
  for (const event of events) {
    if (
      !["agent.delegated", "agent.progress", "agent.completed", "agent.failed"].includes(event.type)
    )
      continue;
    const tid = String(event.payload.task_id ?? "");
    if (!tid) continue;
    if (!groups.has(tid)) order.push(tid);
    const existing = groups.get(tid);
    if (!existing) {
      groups.set(tid, { delegated: null, latest: event });
    } else {
      existing.latest = event;
    }
    if (event.type === "agent.delegated") {
      groups.get(tid)!.delegated = event;
    }
  }
  return order.map((tid) => {
    const group = groups.get(tid)!;
    const delegated = group.delegated;
    const childAgent = String(
      delegated?.payload.child_agent ?? group.latest.payload.child_agent ?? "",
    );
    const capability = String(
      delegated?.payload.capability ?? group.latest.payload.capability ?? "",
    );
    const statusMap: Record<string, TaskSummary["status"]> = {
      "agent.delegated": "delegated",
      "agent.progress": "running",
      "agent.completed": "completed",
      "agent.failed": "failed",
    };
    return {
      taskId: tid,
      childAgent,
      capability,
      status: statusMap[group.latest.type] ?? "delegated",
    };
  });
}

const statusConfig: Record<
  string,
  { icon: typeof CheckCircle2; label: string; tone: string }
> = {
  delegated: {
    icon: Loader2,
    label: "已委派",
    tone: "text-[var(--muted)]",
  },
  running: {
    icon: Loader2,
    label: "执行中",
    tone: "text-[var(--primary)] animate-spin",
  },
  completed: { icon: CheckCircle2, label: "已完成", tone: "text-[var(--success)]" },
  failed: { icon: XCircle, label: "失败", tone: "text-[var(--danger)]" },
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
  const tasks = groupTasks(events);

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-y-auto border-l border-[var(--hairline)] bg-[var(--surface)]">
      {/* Artifacts */}
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

      {/* Sub-agent tasks */}
      <div className="border-t border-[var(--hairline)] p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.66px] text-[var(--muted)]">
          子 Agent 任务
        </h3>
        {tasks.length === 0 ? (
          <p className="mt-2 text-xs text-[var(--muted)]">
            暂无子 Agent 任务。
          </p>
        ) : (
          <div className="mt-2 space-y-1">
            {tasks.map((task) => {
              const IconComp = agentIcons[task.childAgent] ?? Bot;
              const conf = statusConfig[task.status] ?? statusConfig.delegated;
              const StatusIcon = conf.icon;
              return (
                <div
                  className="flex items-center gap-2.5 rounded-[var(--radius-md)] p-2 text-sm"
                  key={`task:${task.taskId}`}
                >
                  <span className="flex size-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-[var(--canvas-soft)] text-[var(--muted)]">
                    <IconComp aria-hidden="true" className="size-3.5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <span className="block truncate text-xs text-[var(--ink)]">
                      {task.capability}
                    </span>
                    <span className="block text-[0.65rem] text-[var(--muted)]">
                      {task.childAgent}
                    </span>
                  </div>
                  <span className={`flex shrink-0 items-center gap-1 text-xs ${conf.tone}`}>
                    <StatusIcon className="size-3" />
                    {conf.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
}
