import { ScorerList } from "@/features/scorers";

export default async function ScorersPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <ScorerList projectId={projectId} />;
}
