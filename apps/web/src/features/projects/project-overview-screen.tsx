"use client";

import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/features/auth";
import { problemKind } from "@/lib/api/problem";

import { getProject, listProjectMembers } from "./api";
import { ProjectOverview } from "./project-overview";

export function ProjectOverviewScreen({ projectId }: { projectId: string }) {
  const userQuery = useQuery({ queryFn: getCurrentUser, queryKey: ["session"] });
  const projectQuery = useQuery({
    queryFn: () => getProject(projectId),
    queryKey: ["project", projectId],
  });
  const membersQuery = useQuery({
    queryFn: () => listProjectMembers(projectId),
    queryKey: ["project-members", projectId],
  });

  if (userQuery.isPending || projectQuery.isPending || membersQuery.isPending) {
    return (
      <ProjectOverview
        loading
        user={{
          display_name: "",
          email: "",
          id: "",
          must_change_password: false,
          role: "viewer",
          status: "active",
        }}
      />
    );
  }

  if (userQuery.isError) {
    return null;
  }

  const queryError = projectQuery.error ?? membersQuery.error;
  if (queryError) {
    const kind = problemKind(queryError);
    return (
      <ProjectOverview
        error={kind === "not-found" || kind === "permission" ? "not-found" : "service"}
        user={userQuery.data}
      />
    );
  }

  return (
    <ProjectOverview
      members={membersQuery.data}
      project={projectQuery.data}
      user={userQuery.data}
    />
  );
}
