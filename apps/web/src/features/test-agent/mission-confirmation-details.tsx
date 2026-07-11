import { CheckCircle2, CircleAlert, ShieldCheck } from "lucide-react";

import type { TestMissionResponse } from "./mission-types";

const channelLabels: Record<string, string> = {
  api: "API 主回归",
  browser: "浏览器关键链路",
  security: "安全基线",
};

const sourceLabels: Record<string, string> = {
  user_provided: "用户提供",
  platform_resolved: "平台匹配",
  target_discovered: "目标探测",
  system_inferred: "系统推断",
};

export function MissionPreviewDetails({
  mission,
}: {
  mission: TestMissionResponse;
}) {
  const budget =
    mission.snapshot && typeof mission.snapshot.budget === "object"
      ? (mission.snapshot.budget as Record<string, unknown>)
      : {};
  return (
    <div className="space-y-3" data-testid="mission-preview-details">
      <div className="flex flex-wrap gap-1.5">
        {mission.execution_channels.map((channel) => (
          <span
            className="rounded-full bg-[var(--info-subtle)] px-2 py-1 text-[0.68rem] font-medium text-[var(--info)]"
            key={channel}
          >
            {channelLabels[channel] ?? channel}
          </span>
        ))}
      </div>
      <div className="space-y-1.5">
        {Object.entries(mission.facts).map(([key, fact]) => (
          <div
            className="flex items-start justify-between gap-3 text-xs"
            key={key}
          >
            <span className="text-[var(--muted)]">{factLabel(key)}</span>
            <span className="min-w-0 text-right text-[var(--ink)]">
              <span className="block truncate">{displayValue(fact.value)}</span>
              <span className="text-[0.65rem] text-[var(--muted)]">
                {sourceLabels[fact.source] ?? fact.source}
                {fact.source === "system_inferred"
                  ? ` · ${Math.round(fact.confidence * 100)}%`
                  : ""}
              </span>
            </span>
          </div>
        ))}
      </div>
      <div className="grid gap-1.5 rounded-lg bg-[var(--canvas-soft)] p-2.5 text-xs text-[var(--muted)]">
        <span className="flex items-center gap-1.5">
          <CheckCircle2 className="size-3.5 text-[var(--success)]" />
          最多 {String(budget.max_cases ?? 50)} 条用例，硬预算{" "}
          {String(budget.hard_cost ?? 20)}
        </span>
        <span className="flex items-center gap-1.5">
          <ShieldCheck className="size-3.5 text-[var(--success)]" />
          允许动作：{mission.action_allowlist.join("、") || "只读"}
        </span>
        <span className="flex items-center gap-1.5 text-[var(--warning)]">
          <CircleAlert className="size-3.5" />
          禁止删除、支付、发布和权限变更；这些操作仍需单独确认
        </span>
      </div>
    </div>
  );
}

function factLabel(key: string) {
  return (
    {
      target: "目标 Agent",
      access: "登录方式",
      test_goal: "测试目标",
      safety_scope: "安全范围",
      scenario_hints: "候选场景",
    }[key] ?? key
  );
}

function displayValue(value: unknown) {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.join("、");
  if (value && typeof value === "object") {
    const object = value as Record<string, unknown>;
    return String(object.url ?? object.strategy ?? "已配置");
  }
  return String(value ?? "-");
}
