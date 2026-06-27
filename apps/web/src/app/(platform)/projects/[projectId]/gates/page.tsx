import { GateList } from "@/features/gates";

export default async function GatesPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <GateList projectId={projectId} />;
}
