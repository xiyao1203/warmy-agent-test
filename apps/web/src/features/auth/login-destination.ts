import type { ProjectResponse } from "@warmy/generated-api-client";

import { projectWorkspacePath } from "@/lib/routes";

import { safeReturnTo } from "./session";

const DEFAULT_LOGIN_RETURN_TO = "/projects";

type ListProjects = () => Promise<ProjectResponse[]>;

export function isProjectScopedReturnTo(path: string) {
  return /^\/projects\/[^/]+(?:\/|$)/.test(path);
}

export function hasProjectScopedReturnTo(returnTo: string | undefined) {
  return isProjectScopedReturnTo(safeReturnTo(returnTo));
}

export function resolveLoginDestinationFromProjects(
  returnTo: string | undefined,
  projects: ProjectResponse[],
) {
  const safePath = safeReturnTo(returnTo);
  if (isProjectScopedReturnTo(safePath)) {
    return safePath;
  }

  const firstProject =
    projects.find((project) => !project.archived) ?? projects[0];
  if (firstProject) {
    return projectWorkspacePath(firstProject.id);
  }

  return DEFAULT_LOGIN_RETURN_TO;
}

export async function resolveLoginDestination(
  returnTo: string | undefined,
  onListProjects: ListProjects,
) {
  const safePath = safeReturnTo(returnTo);
  if (isProjectScopedReturnTo(safePath)) {
    return safePath;
  }

  try {
    return resolveLoginDestinationFromProjects(
      returnTo,
      await onListProjects(),
    );
  } catch {
    return DEFAULT_LOGIN_RETURN_TO;
  }
}
