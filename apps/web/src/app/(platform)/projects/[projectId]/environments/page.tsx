import { EnvironmentListScreen } from "@/features/environments";

export default async function EnvironmentsPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <EnvironmentListScreen projectId={projectId} />;
}
