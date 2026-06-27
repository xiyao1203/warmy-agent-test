import { SecurityScanPage } from "@/features/security";

export default async function SecurityPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <SecurityScanPage projectId={projectId} />;
}
