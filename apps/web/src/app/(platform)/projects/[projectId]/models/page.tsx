import { ModelConfigScreen } from "@/features/model-configs";

export default async function ModelsPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <ModelConfigScreen projectId={projectId} />;
}
