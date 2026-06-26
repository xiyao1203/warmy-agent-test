"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { createProject, listProjects } from "@/features/projects";

export default function ProjectsPage() {
  const router = useRouter();
  const { data: projects, isSuccess, isLoading } = useQuery({
    queryFn: listProjects,
    queryKey: ["projects"],
  });

  useEffect(() => {
    if (isSuccess && projects && projects.length > 0) {
      router.replace(`/projects/${projects[0].id}/overview`);
    }
  }, [isSuccess, projects, router]);

  if (isLoading || (isSuccess && projects && projects.length > 0)) {
    return (
      <main className="grid min-h-screen place-items-center text-sm text-[var(--text-muted)]">
        正在加载…
      </main>
    );
  }

  return (
    <main className="grid min-h-screen place-items-center px-6 text-center">
      <div>
        <h1 className="text-base font-semibold">欢迎使用 AgentTest</h1>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          {isSuccess
            ? "请先创建一个项目以开始使用。"
            : "正在加载…"}
        </p>
        <CreateProjectDialog
          onCreated={(id) => router.replace(`/projects/${id}/overview`)}
        />
      </div>
    </main>
  );
}

function CreateProjectDialog({
  onCreated,
}: {
  onCreated: (projectId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const mutation = useMutation({
    mutationFn: () => createProject({ name: name.trim() }),
    onSuccess: (data) => {
      setOpen(false);
      setName("");
      setError("");
      onCreated(data.id);
    },
    onError: () => {
      setError("创建项目失败，请重试。");
    },
  });

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button className="mt-4" variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建项目
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建项目</DialogTitle>
        <DialogDescription>
          项目是测试资产、运行记录和数据隔离的基本单元。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            项目名称
            <Input
              className="mt-1.5"
              onChange={(event) => {
                setName(event.target.value);
                if (error) setError("");
              }}
              placeholder="例如：画布 Agent 回归测试"
              value={name}
            />
          </label>
          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button onClick={() => setOpen(false)} type="button">
              取消
            </Button>
            <Button
              disabled={!name.trim() || mutation.isPending}
              loading={mutation.isPending}
              onClick={() => mutation.mutate()}
              type="button"
              variant="primary"
            >
              保存项目
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
