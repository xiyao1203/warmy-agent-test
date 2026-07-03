import { AlertTriangle, Bot, CheckCircle2, X } from "lucide-react";
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
  const [busy, setBusy] = useState(false);
  const [decided, setDecided] = useState(false);
  const confirmationId = String(event.payload.confirmation_id);
  const preview = event.payload.preview as Record<string, unknown> | undefined;

  async function decide(approved: boolean) {
    setBusy(true);
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
      setBusy(false);
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

  return (
    <section className="animate-fadeIn overflow-hidden rounded-[var(--radius-lg)] border border-[var(--warning)]/40 bg-[var(--surface)]">
      <div className="flex items-center gap-2.5 border-b border-[var(--hairline)] bg-[var(--warning-subtle)]/30 px-4 py-3">
        <span className="flex size-7 items-center justify-center rounded-full bg-[var(--warning)]/15">
          <AlertTriangle className="size-3.5 text-[var(--warning)]" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-[var(--ink)]">
            需要确认的平台操作
          </p>
          <p className="text-xs text-[var(--muted)]">
            此操作将修改平台数据，请确认后执行
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[0.65rem] font-semibold ${riskMeta.color}`}
        >
          {riskMeta.label}
        </span>
      </div>

      <div className="space-y-2.5 px-4 py-3">
        <div className="flex items-center gap-2.5">
          <Bot className="size-3.5 text-[var(--muted)]" />
          <span className="text-xs text-[var(--muted)]">子 Agent</span>
          <span className="text-xs font-medium text-[var(--ink)]">
            {String(preview?.child_agent ?? "-")}
          </span>
          <span className="text-[0.7rem] text-[var(--hairline)]">·</span>
          <span className="text-xs text-[var(--muted)]">
            {String(preview?.capability ?? "-")}
          </span>
        </div>

        {args && Object.keys(args).length > 0 ? (
          <div className="rounded-[var(--radius-sm)] bg-[var(--canvas-soft)] p-2.5">
            <p className="mb-1.5 text-[0.65rem] font-semibold uppercase tracking-[0.5px] text-[var(--muted)]">
              操作参数
            </p>
            <div className="space-y-1">
              {Object.entries(args).map(([key, value]) => (
                <div className="flex items-start gap-2 text-xs" key={key}>
                  <code className="shrink-0 rounded bg-[var(--surface)] px-1 py-0.5 font-mono text-[var(--primary)]">
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

        {preview?.rationale ? (
          <p className="rounded-[var(--radius-sm)] bg-[var(--canvas-soft)]/50 px-3 py-2 text-xs leading-relaxed text-[var(--muted)] italic">
            {String(preview.rationale)}
          </p>
        ) : null}
      </div>

      <div className="flex justify-end gap-2 border-t border-[var(--hairline)] px-4 py-3">
        <Button
          className="h-8 text-xs"
          disabled={busy}
          onClick={() => void decide(false)}
          variant="secondary"
        >
          <X className="size-3.5" />
          拒绝
        </Button>
        <Button
          className="h-8 text-xs"
          disabled={busy}
          loading={busy}
          onClick={() => void decide(true)}
          variant="primary"
        >
          <CheckCircle2 className="size-3.5" />
          确认执行
        </Button>
      </div>
    </section>
  );
}
