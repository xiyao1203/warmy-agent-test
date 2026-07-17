"use client";

import { CheckCircle2, CircleAlert, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { getRunTrustLoop, type RunTrustLoopData } from "@/features/runs";

import { cancelMission, getMission, resumeMission } from "./api";
import type { MissionProgressOutput } from "./mission-types";
import { TrustLoopResult } from "./trust-loop-result";

export function MissionProgressCard({
  output,
  projectId,
}: {
  output: MissionProgressOutput;
  projectId: string;
}) {
  const [live, setLive] = useState(output);
  const [busy, setBusy] = useState(false);
  const [trustLoop, setTrustLoop] = useState<RunTrustLoopData>();
  useEffect(() => {
    if (["completed", "failed", "cancelled"].includes(live.status)) return;
    let active = true;
    const refresh = () =>
      getMission(projectId, output.mission_id)
        .then((mission) => {
          if (!active) return;
          const run = mission.assets?.find((asset) => asset.type === "run");
          setLive((current) => ({
            ...current,
            status: mission.status,
            workflow_id: mission.workflow_id ?? undefined,
            run_id: run?.id ?? current.run_id,
          }));
        })
        .catch(() => undefined);
    void refresh();
    const timer = window.setInterval(refresh, 2000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [live.status, output.mission_id, projectId]);
  useEffect(() => {
    if (!live.run_id) return;
    let active = true;
    let timer: number | undefined;
    const refresh = async () => {
      try {
        const value = await getRunTrustLoop(projectId, live.run_id!);
        if (!active) return;
        setTrustLoop(value);
        if (["pending", "running"].includes(value.summary.status)) {
          timer = window.setTimeout(refresh, 2000);
        }
      } catch {
        if (active) timer = window.setTimeout(refresh, 2000);
      }
    };
    void refresh();
    return () => {
      active = false;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [live.run_id, projectId]);
  const terminal = ["completed", "failed", "cancelled"].includes(live.status);
  const failed = live.status === "failed";
  const needsAttention = live.status === "needs_attention";
  const Icon = failed ? CircleAlert : terminal ? CheckCircle2 : Loader2;
  const label = needsAttention
    ? "登录态已失效，请在浏览器实例重新登录后继续"
    : failed
      ? "全链路测试需要处理"
      : terminal
        ? "全链路测试已完成"
        : "全链路测试执行中";
  return (
    <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface)] p-3">
      <div className="flex items-center gap-2">
        <Icon
          className={`size-4 ${failed ? "text-[var(--danger)]" : "text-[var(--primary)]"} ${terminal ? "" : "animate-spin"}`}
        />
        <span className="text-sm font-medium text-[var(--ink)]">{label}</span>
      </div>
      {live.missing_fields?.length ? (
        <p className="mt-2 text-xs text-[var(--warning)]">
          还需提供：{live.missing_fields.join("、")}
        </p>
      ) : null}
      {live.run_id ? (
        <Link
          className="mt-2 inline-flex text-xs font-medium text-[var(--primary)] hover:underline"
          href={`/projects/${projectId}/runs/${live.run_id}`}
        >
          查看运行详情
        </Link>
      ) : null}
      <div className="mt-2 flex gap-2">
        {needsAttention ? (
          <button
            className="rounded-[var(--radius-sm)] bg-[var(--primary)] px-2 py-1 text-xs text-[var(--on-primary)] disabled:opacity-50"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                const mission = await resumeMission(
                  projectId,
                  output.mission_id,
                );
                setLive((current) => ({ ...current, status: mission.status }));
              } finally {
                setBusy(false);
              }
            }}
            type="button"
          >
            登录完成，继续测试
          </button>
        ) : null}
        {!terminal && !needsAttention ? (
          <button
            className="rounded-md border border-[var(--hairline)] px-2 py-1 text-xs disabled:opacity-50"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                const mission = await cancelMission(
                  projectId,
                  output.mission_id,
                );
                setLive((current) => ({ ...current, status: mission.status }));
              } finally {
                setBusy(false);
              }
            }}
            type="button"
          >
            取消测试
          </button>
        ) : null}
      </div>
      {live.run_id ? (
        <TrustLoopResult
          data={trustLoop}
          loading={!trustLoop}
          projectId={projectId}
          runId={live.run_id}
        />
      ) : null}
    </div>
  );
}
