"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import type { RenameProjectRequest } from "@warmy/generated-api-client";

import {
  archiveProject,
  createProject,
  listProjectPage,
  ProjectListScreen,
  renameProject,
} from "@/features/projects";
import { projectWorkspacePath } from "@/lib/routes";
import { usePaginationState } from "@/lib/use-pagination-state";

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const pagination = usePaginationState();
  const projectsQuery = useQuery({
    queryFn: () => listProjectPage(pagination.page, pagination.pageSize),
    queryKey: ["projects", pagination.page, pagination.pageSize],
    placeholderData: keepPreviousData,
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
      onPageChange={pagination.setPage}
      onPageSizeChange={pagination.setPageSize}
      onRename={(projectId, payload) =>
        renameMutation.mutateAsync({ payload, projectId })
      }
      page={projectsQuery.data?.page ?? pagination.page}
      pageSize={pagination.pageSize}
      projects={projectsQuery.data?.items ?? []}
      total={projectsQuery.data?.total ?? 0}
      totalPages={projectsQuery.data?.total_pages ?? 0}
    />
  );
}
