import { AlertTriangle, Bot, CheckCircle2, ChevronDown, X } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

import { decideConfirmation, previewMission } from "./api";
import type { AgentEvent } from "./api";
import { MissionPreviewDetails } from "./mission-confirmation-details";
import type { TestMissionResponse } from "./mission-types";

export function ConfirmationCard({
  event,
  projectId,
  sessionId,
  onDecided,
}: {
  event: AgentEvent;
  projectId: string;
  sessionId: string;
  onDecided: () => void;
}) {
  const [decision, setDecision] = useState<"approve" | "reject" | null>(null);
  const [decided, setDecided] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const confirmationId = String(event.payload.confirmation_id);
  const preview = event.payload.preview as Record<string, unknown> | undefined;
  const capability = String(preview?.capability ?? "");
  const args = preview?.arguments as Record<string, unknown> | undefined;
  const missionConfirmation = capability === "test_missions.confirm_and_start";
  const missionId = String(args?.mission_id ?? "");
  const [mission, setMission] = useState<TestMissionResponse | null>(null);
  const [missionError, setMissionError] = useState<string | null>(null);

  useEffect(() => {
    if (!missionConfirmation || !missionId) return;
    let active = true;
    previewMission(projectId, missionId)
      .then((result) => {
        if (active) setMission(result);
      })
      .catch((error: unknown) => {
        if (active)
          setMissionError(
            error instanceof Error ? error.message : "执行预览加载失败",
          );
      });
    return () => {
      active = false;
    };
  }, [missionConfirmation, missionId, projectId]);

  async function decide(approved: boolean) {
    setDecision(approved ? "approve" : "reject");
    try {
      await decideConfirmation(
        projectId,
        sessionId,
        confirmationId,
        approved,
        String(event.payload.generation_id ?? "") || undefined,
      );
      setDecided(true);
      onDecided();
    } finally {
      setDecision(null);
    }
  }

  if (decided) return null;

  const riskLabels: Record<string, { label: string; color: string }> = {
    HIGH_IMPACT: {
      label: "高风险",
      color: "text-[var(--danger)] bg-[var(--danger-subtle)]",
    },
    DRAFT_WRITE: {
      label: "写入",
      color: "text-[var(--warning)] bg-[var(--warning-subtle)]",
    },
    READ: {
      label: "只读",
      color: "text-[var(--info)] bg-[var(--info-subtle)]",
    },
  };
  const risk = String(preview?.risk ?? "DRAFT_WRITE");
  const riskMeta = riskLabels[risk] ?? riskLabels.DRAFT_WRITE;
  const hasArgs = Boolean(args && Object.keys(args).length > 0);
  const busy = decision !== null;

  return (
    <section className="overflow-hidden border-l border-[var(--warning)] pl-4">
      <div className="flex items-start gap-3 py-1.5">
        <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-[var(--warning-subtle)]">
          <AlertTriangle className="size-3.5 text-[var(--warning)]" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-[var(--ink)]">
            {missionConfirmation
              ? "确认并开始全链路测试"
              : `确认执行 ${String(preview?.capability ?? "平台操作")}`}
          </p>
          <p className="mt-0.5 text-xs leading-5 text-[var(--muted)]">
            {missionConfirmation
              ? "确认后自动创建或复用测试资产并启动真实运行"
              : `${String(preview?.child_agent ?? "子 Agent")} 将修改平台数据`}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[0.65rem] font-semibold ${riskMeta.color}`}
        >
          {missionConfirmation ? "一次确认" : riskMeta.label}
        </span>
      </div>

      <div className="ml-10 space-y-2 pb-2">
        {missionConfirmation ? (
          mission ? (
            <MissionPreviewDetails mission={mission} />
          ) : missionError ? (
            <p className="text-xs text-[var(--danger)]">{missionError}</p>
          ) : (
            <p className="text-xs text-[var(--muted)]">
              正在加载不可变执行预览…
            </p>
          )
        ) : null}
        <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
          <Bot className="size-3.5 text-[var(--muted)]" />
          <span>子 Agent</span>
          <span className="font-medium text-[var(--ink)]">
            {String(preview?.child_agent ?? "-")}
          </span>
        </div>

        {hasArgs && !missionConfirmation ? (
          <div>
            <button
              aria-expanded={expanded}
              className="flex min-h-9 items-center gap-1.5 rounded-lg px-2 text-xs font-medium text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
              onClick={() => setExpanded((value) => !value)}
              type="button"
            >
              查看参数
              <ChevronDown
                className={`size-3.5 transition-transform ${expanded ? "rotate-180" : ""}`}
              />
            </button>
            {expanded ? (
              <div className="rounded-lg bg-[var(--canvas-soft)] p-2.5">
                <div className="space-y-1">
                  {Object.entries(args ?? {}).map(([key, value]) => (
                    <div className="flex items-start gap-2 text-xs" key={key}>
                      <code className="shrink-0 font-mono text-[var(--body)]">
                        {key}
                      </code>
                      <span className="break-all text-[var(--muted)]">
                        {typeof value === "object"
                          ? JSON.stringify(value)
                          : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}

        {preview?.rationale ? (
          <p className="text-xs leading-5 text-[var(--muted)]">
            {String(preview.rationale)}
          </p>
        ) : null}
      </div>

      <div className="ml-10 flex flex-wrap gap-2 pb-2">
        <Button
          className="h-8 text-xs"
          disabled={busy || (missionConfirmation && !mission)}
          onClick={() => void decide(false)}
          variant="secondary"
        >
          <X className="size-3.5" />
          {decision === "reject" ? "正在拒绝" : "拒绝"}
        </Button>
        <Button
          className="h-8 text-xs"
          disabled={busy}
          loading={decision === "approve"}
          onClick={() => void decide(true)}
          variant="primary"
        >
          <CheckCircle2 className="size-3.5" />
          {decision === "approve"
            ? "正在执行"
            : missionConfirmation
              ? "确认并开始测试"
              : "确认执行"}
        </Button>
      </div>
    </section>
  );
}
