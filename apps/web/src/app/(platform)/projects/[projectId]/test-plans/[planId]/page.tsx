import { TestPlanDetailScreen } from "@/features/test-plans";

export default async function TestPlanDetailPage({
  params,
}: {
  params: Promise<{ planId: string; projectId: string }>;
}) {
  const { planId, projectId } = await params;
  return <TestPlanDetailScreen planId={planId} projectId={projectId} />;
}
