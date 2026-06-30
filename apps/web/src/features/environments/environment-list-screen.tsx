"use client";

import { useQuery } from "@tanstack/react-query";

import {
  createEnvironmentTemplate,
  deleteEnvironmentTemplate,
  listEnvironmentTemplates,
} from "./api";
import { EnvironmentList } from "./environment-list";

export function EnvironmentListScreen({ projectId }: { projectId: string }) {
  const envQuery = useQuery({
    queryFn: () => listEnvironmentTemplates(projectId),
    queryKey: ["environment-templates", projectId],
  });

  if (envQuery.isPending) {
    return <EnvironmentList loading projectId={projectId} />;
  }
  if (envQuery.isError) {
    return <EnvironmentList error="service" projectId={projectId} />;
  }

  async function refresh() {
    await envQuery.refetch();
  }

  return (
    <EnvironmentList
      environments={envQuery.data ?? []}
      onCreate={async (payload) => {
        await createEnvironmentTemplate(projectId, payload);
        await refresh();
      }}
      onDelete={async (templateId) => {
        await deleteEnvironmentTemplate(projectId, templateId);
        await refresh();
      }}
      projectId={projectId}
    />
  );
}
