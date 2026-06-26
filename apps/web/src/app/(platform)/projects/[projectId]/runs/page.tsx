import { RunCenterScreen } from "@/features/runs";

export default async function RunsPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <RunCenterScreen projectId={projectId} />;
}

