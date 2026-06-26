"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { cancelRun, getRun, listArtifacts, listRunCases, runEventsUrl } from "./api";
import { RunDetail } from "./run-detail";

/** SSE 重连配置 */
const MAX_RECONNECT_ATTEMPTS = 3;
const INITIAL_RECONNECT_MS = 1000;
const MAX_RECONNECT_MS = 10000;

export function RunDetailScreen({
  projectId,
  runId,
}: {
  projectId: string;
  runId: string;
}) {
  const streamKey = `${projectId}:${runId}`;
  const [failedStreamKey, setFailedStreamKey] = useState<string | null>(null);
  const [reconnectTick, setReconnectTick] = useState(0);
  const eventStreamFailed = failedStreamKey === streamKey;
  const eventStreamAvailable =
    !eventStreamFailed && typeof EventSource !== "undefined";
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const runQuery = useQuery({
    queryFn: () => getRun(projectId, runId),
    queryKey: ["runs", projectId, runId],
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status !== "running" && status !== "queued") {
        return false;
      }
      return eventStreamAvailable ? false : 3000;
    },
  });
  const casesQuery = useQuery({
    queryFn: () => listRunCases(projectId, runId),
    queryKey: ["runs", projectId, runId, "cases"],
  });
  const artifactsQuery = useQuery({
    queryFn: () => listArtifacts(projectId, runId),
    queryKey: ["runs", projectId, runId, "artifacts"],
  });
  const runStatus = runQuery.data?.status;
  const refetchRun = runQuery.refetch;
  const refetchCases = casesQuery.refetch;

  /** 清理重连计时器 */
  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  /** 切换运行时重置 SSE 状态 */
  useEffect(() => {
    reconnectAttemptRef.current = 0;
    clearReconnectTimer();
  }, [clearReconnectTimer, streamKey]);

  /** 建立 SSE 连接（含退避重连） */
  useEffect(() => {
    if (
      !eventStreamAvailable ||
      (runStatus !== "running" && runStatus !== "queued") ||
      typeof EventSource === "undefined"
    ) {
      clearReconnectTimer();
      return;
    }

    const source = new EventSource(runEventsUrl(projectId, runId));

    source.onopen = () => {
      // 连接成功，重置重连计数
      reconnectAttemptRef.current = 0;
      clearReconnectTimer();
    };

    source.onmessage = () => {
      void refetchRun();
      void refetchCases();
    };

    source.onerror = () => {
      source.close();
      clearReconnectTimer();

      const attempts = reconnectAttemptRef.current;
      if (attempts < MAX_RECONNECT_ATTEMPTS) {
        // 指数退避重连：1s, 2s, 4s, 最大 10s
        const delay = Math.min(
          INITIAL_RECONNECT_MS * Math.pow(2, attempts),
          MAX_RECONNECT_MS,
        );
        reconnectAttemptRef.current = attempts + 1;
        reconnectTimerRef.current = setTimeout(() => {
          // 显式触发 useEffect 重建 EventSource
          setReconnectTick((tick) => tick + 1);
        }, delay);
      } else {
        // 超过最大重连次数，回退到轮询
        setFailedStreamKey(streamKey);
      }
    };

    return () => {
      source.close();
      clearReconnectTimer();
    };
  }, [
    clearReconnectTimer,
    eventStreamAvailable,
    projectId,
    refetchCases,
    refetchRun,
    reconnectTick,
    runId,
    runStatus,
    streamKey,
  ]);
  const cancelMutation = useMutation({
    mutationFn: () => cancelRun(projectId, runId),
    onSuccess: async () => {
      await runQuery.refetch();
      await casesQuery.refetch();
    },
  });
  return (
    <RunDetail
      artifacts={artifactsQuery.data ?? []}
      cases={casesQuery.data ?? []}
      loading={runQuery.isPending || casesQuery.isPending}
      onCancel={() => cancelMutation.mutateAsync()}
      projectId={projectId}
      run={runQuery.data}
    />
  );
}
