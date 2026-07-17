"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { problemKind } from "@/lib/api/problem";

import { createTestPlan, deleteTestPlan } from "./api";
import { TestPlanList } from "./test-plan-list";
import { invalidateTestPlanList, testPlanQueries } from "./queries";

export function TestPlanListScreen({ projectId }: { projectId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const plansQuery = useQuery(testPlanQueries.list(projectId));
  if (plansQuery.isPending) {
    return <TestPlanList loading projectId={projectId} />;
  }
  if (plansQuery.isError) {
    const kind = problemKind(plansQuery.error);
    return (
      <TestPlanList
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
    <TestPlanList
      onCreate={async (payload) => {
        const plan = await createTestPlan(projectId, payload);
        await invalidateTestPlanList(queryClient, projectId);
        if (plan?.id) {
          router.push(`/projects/${projectId}/test-plans/${plan.id}`);
        }
      }}
      onDelete={async (planId) => {
        await deleteTestPlan(projectId, planId);
        await invalidateTestPlanList(queryClient, projectId);
      }}
      plans={plansQuery.data.items}
      projectId={projectId}
    />
  );
}
