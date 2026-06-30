import { RunDetailScreen } from "@/features/runs";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ projectId: string; runId: string }>;
}) {
  const { projectId, runId } = await params;
  return <RunDetailScreen projectId={projectId} runId={runId} />;
}
