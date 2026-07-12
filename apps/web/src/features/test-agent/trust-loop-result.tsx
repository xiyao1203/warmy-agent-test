import { TrustLoopPanel, type RunTrustLoopData } from "@/features/runs";

export function TrustLoopResult({
  data,
  loading = false,
  projectId,
  runId,
}: {
  data?: RunTrustLoopData;
  loading?: boolean;
  projectId: string;
  runId: string;
}) {
  return (
    <TrustLoopPanel
      compact
      data={data}
      loading={loading}
      projectId={projectId}
      runId={runId}
    />
  );
}
