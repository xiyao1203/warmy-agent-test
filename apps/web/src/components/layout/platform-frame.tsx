"use client";

import { useQuery } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useCallback, useEffect, useState } from "react";

import { getCurrentUser } from "@/features/auth";
import { listProjects } from "@/features/projects";

import { AppShell } from "./app-shell";

const PROJECT_STORAGE_KEY = "agenttest_current_project_id";

export function PlatformFrame({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const userQuery = useQuery({
    queryFn: getCurrentUser,
    queryKey: ["session"],
  });
  const projectsQuery = useQuery({
    enabled: userQuery.isSuccess,
    queryFn: listProjects,
    queryKey: ["projects"],
  });

  const urlProjectId = pathname.match(/^\/projects\/([^/]+)/)?.[1];

  const [storedProjectId, setStoredProjectId] = useState<string | undefined>(
    () => {
      if (typeof window !== "undefined") {
        return localStorage.getItem(PROJECT_STORAGE_KEY) ?? undefined;
      }
      return undefined;
    },
  );

  useEffect(() => {
    if (urlProjectId) {
      localStorage.setItem(PROJECT_STORAGE_KEY, urlProjectId);
    }
  }, [urlProjectId]);

  const projects = projectsQuery.data ?? [];
  const currentProjectId =
    urlProjectId ??
    storedProjectId ??
    (projects.length > 0 ? projects[0].id : undefined);

  const handleProjectSelect = useCallback(
    (projectId: string) => {
      localStorage.setItem(PROJECT_STORAGE_KEY, projectId);
      setStoredProjectId(projectId);
      router.push(`/projects/${projectId}/overview`);
    },
    [router],
  );

  if (userQuery.isPending || projectsQuery.isPending) {
    return (
      <main className="grid min-h-screen place-items-center text-sm text-[var(--muted)]">
        正在加载工作台…
      </main>
    );
  }

  if (userQuery.isError) {
    const returnTo = encodeURIComponent(pathname);
    router.replace(`/login?returnTo=${returnTo}`);
    return null;
  }

  if (projectsQuery.isError) {
    return (
      <main className="grid min-h-screen place-items-center px-6 text-center">
        <div>
          <h1 className="text-base font-semibold">无法加载项目</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            请检查网络连接后刷新页面。
          </p>
        </div>
      </main>
    );
  }

  return (
    <AppShell
      currentProjectId={currentProjectId}
      onProjectSelect={handleProjectSelect}
      projects={projects}
      user={userQuery.data}
    >
      {children}
    </AppShell>
  );
}
