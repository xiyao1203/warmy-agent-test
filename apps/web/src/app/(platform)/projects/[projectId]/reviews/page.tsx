import { ReviewWorkbench } from "@/features/reviews";

export default async function ReviewsPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <ReviewWorkbench projectId={projectId} />;
}
