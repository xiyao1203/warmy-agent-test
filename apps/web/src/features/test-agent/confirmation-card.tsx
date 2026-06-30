import { ShieldCheck, X } from "lucide-react";
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
      await decideConfirmation(projectId, sessionId, confirmationId, approved);
      setDecided(true);
      onDecided();
    } finally {
      setBusy(false);
    }
  }

  if (decided) return null;
  return (
    <section className="rounded-[var(--radius-md)] border border-[var(--warning)] bg-[var(--warning-subtle)] p-4">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <ShieldCheck className="size-4" />
        需要确认的平台操作
      </div>
      <dl className="mt-3 grid grid-cols-[7rem_1fr] gap-2 text-xs">
        <dt className="text-[var(--text-muted)]">子 Agent</dt>
        <dd>{String(preview?.child_agent ?? "-")}</dd>
        <dt className="text-[var(--text-muted)]">能力</dt>
        <dd>{String(preview?.capability ?? "-")}</dd>
        <dt className="text-[var(--text-muted)]">原因</dt>
        <dd>{String(preview?.rationale ?? "-")}</dd>
      </dl>
      <div className="mt-4 flex justify-end gap-2">
        <Button disabled={busy} onClick={() => void decide(false)} variant="secondary">
          <X className="size-4" />
          拒绝
        </Button>
        <Button disabled={busy} loading={busy} onClick={() => void decide(true)} variant="primary">
          确认执行
        </Button>
      </div>
    </section>
  );
}
