import { ExperimentList } from "@/features/experiments";

export default async function ExperimentsPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <ExperimentList projectId={projectId} />;
}
