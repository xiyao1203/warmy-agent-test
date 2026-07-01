"use client";

import { useQuery } from "@tanstack/react-query";

import {
  createEnvironmentTemplate,
  createEnvironmentVersion,
  deleteEnvironmentTemplate,
  listEnvironmentTemplates,
  publishEnvironmentVersion,
  updateEnvironmentVersion,
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
      onCreateVersion={async (templateId, payload) => {
        const result = await createEnvironmentVersion(
          projectId,
          templateId,
          payload,
        );
        await refresh();
        return result;
      }}
      onDelete={async (templateId) => {
        await deleteEnvironmentTemplate(projectId, templateId);
        await refresh();
      }}
      onPublishVersion={async (templateId, versionId) => {
        const result = await publishEnvironmentVersion(
          projectId,
          templateId,
          versionId,
        );
        await refresh();
        return result;
      }}
      onUpdateVersion={async (templateId, versionId, payload) => {
        const result = await updateEnvironmentVersion(
          projectId,
          templateId,
          versionId,
          payload,
        );
        await refresh();
        return result;
      }}
      projectId={projectId}
    />
  );
}
