import { TestAgentChat } from "@/features/test-agent";

export default async function TestAgentPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <TestAgentChat projectId={projectId} />;
}
