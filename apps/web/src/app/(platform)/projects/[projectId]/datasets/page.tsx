import { DatasetListScreen } from "@/features/datasets";

export default async function DatasetsPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <DatasetListScreen projectId={projectId} />;
}
