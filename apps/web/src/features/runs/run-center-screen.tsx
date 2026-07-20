"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { problemKind } from "@/lib/api/problem";
import { usePaginationState } from "@/lib/use-pagination-state";

import { createRun } from "./api";
import { RunCenter } from "./run-center";
import { invalidateRunList, runQueries } from "./queries";

export function RunCenterScreen({ projectId }: { projectId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const pagination = usePaginationState();
  const runsQuery = useQuery(
    runQueries.list(projectId, pagination.page, pagination.pageSize),
  );
  const versionsQuery = useQuery(runQueries.publishedPlanVersions(projectId));
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
        await invalidateRunList(queryClient, projectId);
        if (run?.id) {
          router.push(`/projects/${projectId}/runs/${run.id}`);
        }
        return run;
      }}
      onPageChange={pagination.setPage}
      onPageSizeChange={pagination.setPageSize}
      page={runsQuery.data.page ?? pagination.page}
      pageSize={pagination.pageSize}
      planVersions={versionsQuery.data}
      projectId={projectId}
      runs={runsQuery.data.items}
      total={runsQuery.data.total}
      totalPages={runsQuery.data.total_pages}
    />
  );
}
