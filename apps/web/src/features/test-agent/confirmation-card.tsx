import { AlertTriangle, Bot, CheckCircle2, ChevronDown, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { decideConfirmation } from "./api";
import type { AgentEvent } from "./api";

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
  const args = preview?.arguments as Record<string, unknown> | undefined;
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
            确认执行 {String(preview?.capability ?? "平台操作")}
          </p>
          <p className="mt-0.5 text-xs leading-5 text-[var(--muted)]">
            {String(preview?.child_agent ?? "子 Agent")} 将修改平台数据
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[0.65rem] font-semibold ${riskMeta.color}`}
        >
          {riskMeta.label}
        </span>
      </div>

      <div className="ml-10 space-y-2 pb-2">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
          <Bot className="size-3.5 text-[var(--muted)]" />
          <span>子 Agent</span>
          <span className="font-medium text-[var(--ink)]">
            {String(preview?.child_agent ?? "-")}
          </span>
        </div>

        {hasArgs ? (
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
          disabled={busy}
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
          {decision === "approve" ? "正在执行" : "确认执行"}
        </Button>
      </div>
    </section>
  );
}
