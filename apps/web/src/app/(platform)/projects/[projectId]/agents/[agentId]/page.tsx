import { AgentDetailScreen } from "@/features/agents";

export default async function AgentDetailPage({
  params,
}: {
  params: Promise<{ agentId: string; projectId: string }>;
}) {
  const { agentId, projectId } = await params;
  return <AgentDetailScreen agentId={agentId} projectId={projectId} />;
}
