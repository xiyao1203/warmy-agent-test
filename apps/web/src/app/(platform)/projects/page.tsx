"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { listProjects } from "@/features/projects";

export default function ProjectsPage() {
  const router = useRouter();
  const { data: projects, isSuccess } = useQuery({
    queryFn: listProjects,
    queryKey: ["projects"],
  });

  if (isSuccess && projects && projects.length > 0) {
    router.replace(`/projects/${projects[0].id}/overview`);
    return null;
  }

  return (
    <main className="grid min-h-screen place-items-center px-6 text-center">
      <div>
        <h1 className="text-base font-semibold">欢迎使用 AgentTest</h1>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          {isSuccess ? "请先创建一个项目以开始使用。" : "正在加载…"}
        </p>
      </div>
    </main>
  );
}
