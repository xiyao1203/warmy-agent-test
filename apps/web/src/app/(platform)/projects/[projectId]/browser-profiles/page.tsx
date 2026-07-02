import { BrowserProfileListScreen } from "@/features/browser-profiles";

export default async function BrowserProfilesPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <BrowserProfileListScreen projectId={projectId} />;
}
