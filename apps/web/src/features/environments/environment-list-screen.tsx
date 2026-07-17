"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createEnvironmentTemplate,
  createEnvironmentVersion,
  deleteEnvironmentTemplate,
  publishEnvironmentVersion,
  updateEnvironmentVersion,
} from "./api";
import { EnvironmentList } from "./environment-list";
import { environmentQueries, invalidateEnvironmentList } from "./queries";

export function EnvironmentListScreen({ projectId }: { projectId: string }) {
  const envQuery = useQuery(environmentQueries.list(projectId));
  const queryClient = useQueryClient();

  if (envQuery.isPending) {
    return <EnvironmentList loading projectId={projectId} />;
  }
  if (envQuery.isError) {
    return <EnvironmentList error="service" projectId={projectId} />;
  }

  async function refresh() {
    await invalidateEnvironmentList(queryClient, projectId);
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
