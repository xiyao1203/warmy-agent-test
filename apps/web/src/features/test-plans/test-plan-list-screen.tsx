"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { problemKind } from "@/lib/api/problem";

import { createTestPlan, deleteTestPlan, listTestPlans } from "./api";
import { TestPlanList } from "./test-plan-list";

export function TestPlanListScreen({ projectId }: { projectId: string }) {
  const router = useRouter();
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
        const plan = await createTestPlan(projectId, payload);
        await plansQuery.refetch();
        if (plan?.id) {
          router.push(`/projects/${projectId}/test-plans/${plan.id}`);
        }
      }}
      onDelete={async (planId) => {
        await deleteTestPlan(projectId, planId);
        await plansQuery.refetch();
      }}
      plans={plansQuery.data.items}
      projectId={projectId}
    />
  );
}
