"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { problemKind } from "@/lib/api/problem";

import { createRun, listPublishedPlanVersions, listRuns } from "./api";
import { RunCenter } from "./run-center";

export function RunCenterScreen({ projectId }: { projectId: string }) {
  const router = useRouter();
  const runsQuery = useQuery({
    queryFn: () => listRuns(projectId),
    queryKey: ["runs", projectId],
    refetchInterval: 5000,
  });
  const versionsQuery = useQuery({
    queryFn: () => listPublishedPlanVersions(projectId),
    queryKey: ["runs", projectId, "published-plan-versions"],
  });
  if (runsQuery.isPending || versionsQuery.isPending) {
    return <RunCenter loading projectId={projectId} />;
  }
  if (runsQuery.isError || versionsQuery.isError) {
    const error = runsQuery.error ?? versionsQuery.error;
    const kind = problemKind(error);
    return (
      <RunCenter
        error={
          kind === "not-found" || kind === "permission"
            ? "not-found"
            : "service"
        }
        projectId={projectId}
      />
    );
  }
  return (
    <RunCenter
      onCreate={async (versionId) => {
        const run = await createRun(projectId, versionId);
        await runsQuery.refetch();
        if (run?.id) {
          router.push(`/projects/${projectId}/runs/${run.id}`);
        }
        return run;
      }}
      planVersions={versionsQuery.data}
      projectId={projectId}
      runs={runsQuery.data}
    />
  );
}
