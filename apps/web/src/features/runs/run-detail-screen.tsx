"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { cancelRun, getRun, listRunCases, runEventsUrl } from "./api";
import { RunDetail } from "./run-detail";

export function RunDetailScreen({
  projectId,
  runId,
}: {
  projectId: string;
  runId: string;
}) {
  const [eventStreamFailed, setEventStreamFailed] = useState(false);
  const eventStreamAvailable =
    !eventStreamFailed && typeof EventSource !== "undefined";
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
  useEffect(() => {
    const status = runQuery.data?.status;
    if (
      !eventStreamAvailable ||
      (status !== "running" && status !== "queued") ||
      typeof EventSource === "undefined"
    ) {
      return;
    }
    const source = new EventSource(runEventsUrl(projectId, runId));
    source.onmessage = () => {
      void runQuery.refetch();
      void casesQuery.refetch();
    };
    source.onerror = () => {
      source.close();
      setEventStreamFailed(true);
    };
    return () => {
      source.close();
    };
  }, [
    casesQuery,
    eventStreamAvailable,
    projectId,
    runId,
    runQuery,
    runQuery.data?.status,
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
      cases={casesQuery.data ?? []}
      loading={runQuery.isPending || casesQuery.isPending}
      onCancel={() => cancelMutation.mutateAsync()}
      run={runQuery.data}
    />
  );
}
