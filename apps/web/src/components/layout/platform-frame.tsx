"use client";

import { useQuery } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { getCurrentUser } from "@/features/auth";
import { listProjects } from "@/features/projects";

import { AppShell } from "./app-shell";

export function PlatformFrame({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const userQuery = useQuery({ queryFn: getCurrentUser, queryKey: ["session"] });
  const projectsQuery = useQuery({
    enabled: userQuery.isSuccess,
    queryFn: listProjects,
    queryKey: ["projects"],
  });
  const currentProjectId = pathname.match(/^\/projects\/([^/]+)/)?.[1];

  if (userQuery.isPending || projectsQuery.isPending) {
    return (
      <main className="grid min-h-screen place-items-center text-sm text-[var(--text-muted)]">
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
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            请检查网络连接后刷新页面。
          </p>
        </div>
      </main>
    );
  }

  return (
    <AppShell
      currentProjectId={currentProjectId}
      onProjectSelect={(projectId) =>
        router.push(`/projects/${projectId}/overview`)
      }
      projects={projectsQuery.data}
      user={userQuery.data}
    >
      {children}
    </AppShell>
  );
}
