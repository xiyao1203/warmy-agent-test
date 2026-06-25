import { AgentListScreen } from "@/features/agents";

export default async function AgentsPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <AgentListScreen projectId={projectId} />;
}
