import { ProjectOverviewScreen } from "@/features/projects";

export default async function ProjectOverviewPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <ProjectOverviewScreen projectId={projectId} />;
}
