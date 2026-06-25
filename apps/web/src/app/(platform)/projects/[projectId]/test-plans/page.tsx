import { TestPlanListScreen } from "@/features/test-plans";

export default async function TestPlansPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <TestPlanListScreen projectId={projectId} />;
}
