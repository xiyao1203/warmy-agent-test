import { DatasetDetailScreen } from "@/features/datasets";

export default async function DatasetDetailPage({
  params,
}: {
  params: Promise<{ datasetId: string; projectId: string }>;
}) {
  const { datasetId, projectId } = await params;
  return <DatasetDetailScreen datasetId={datasetId} projectId={projectId} />;
}
