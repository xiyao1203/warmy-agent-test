"use client";

import { useQuery } from "@tanstack/react-query";

import { problemKind } from "@/lib/api/problem";

import { createTestPlan, listTestPlans } from "./api";
import { TestPlanList } from "./test-plan-list";

export function TestPlanListScreen({ projectId }: { projectId: string }) {
  const plansQuery = useQuery({
    queryFn: () => listTestPlans(projectId),
    queryKey: ["test-plans", projectId],
  });
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
        await createTestPlan(projectId, payload);
        await plansQuery.refetch();
      }}
      plans={plansQuery.data.items}
      projectId={projectId}
    />
  );
}
