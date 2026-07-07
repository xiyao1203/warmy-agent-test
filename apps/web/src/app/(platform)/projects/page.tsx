"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import type { RenameProjectRequest } from "@warmy/generated-api-client";

import {
  archiveProject,
  createProject,
  listProjects,
  ProjectListScreen,
  renameProject,
} from "@/features/projects";
import { projectWorkspacePath } from "@/lib/routes";

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const projectsQuery = useQuery({
    queryFn: listProjects,
    queryKey: ["projects"],
  });

  const refreshProjects = () =>
    queryClient.invalidateQueries({ queryKey: ["projects"] });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: refreshProjects,
  });
  const renameMutation = useMutation({
    mutationFn: ({
      payload,
      projectId,
    }: {
      payload: RenameProjectRequest;
      projectId: string;
    }) => renameProject(projectId, payload),
    onSuccess: refreshProjects,
  });
  const archiveMutation = useMutation({
    mutationFn: archiveProject,
    onSuccess: refreshProjects,
  });

  return (
    <ProjectListScreen
      error={projectsQuery.isError ? "service" : undefined}
      loading={projectsQuery.isLoading}
      onArchive={(projectId) => archiveMutation.mutateAsync(projectId)}
      onCreate={(payload) => createMutation.mutateAsync(payload)}
      onOpen={(projectId) => router.push(projectWorkspacePath(projectId))}
      onRename={(projectId, payload) =>
        renameMutation.mutateAsync({ payload, projectId })
      }
      projects={projectsQuery.data ?? []}
    />
  );
}
