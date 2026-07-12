"use client";

import * as Popover from "@radix-ui/react-popover";
import type { ProjectResponse } from "@warmy/generated-api-client";
import { Check, ChevronsUpDown, FolderArchive } from "lucide-react";
import { useMemo, useState } from "react";

import { Input } from "@/components/ui/input";

type ProjectSwitcherProps = {
  currentProjectId?: string;
  onSelect: (projectId: string) => void;
  projects: ProjectResponse[];
};

export function ProjectSwitcher({
  currentProjectId,
  onSelect,
  projects,
}: ProjectSwitcherProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const currentProject = projects.find(
    (project) => project.id === currentProjectId,
  );
  const filteredProjects = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    return normalized
      ? projects.filter((project) =>
          project.name.toLocaleLowerCase().includes(normalized),
        )
      : projects;
  }, [projects, query]);

  return (
    <Popover.Root onOpenChange={setOpen} open={open}>
      <Popover.Trigger asChild>
        <button
          className="flex h-8 min-w-44 max-w-64 items-center justify-between gap-2 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-2.5 text-sm hover:bg-[var(--canvas-soft)] max-sm:w-28 max-sm:min-w-0"
          type="button"
        >
          <span className="truncate">{currentProject?.name ?? "选择项目"}</span>
          <ChevronsUpDown
            aria-hidden="true"
            className="size-3.5 shrink-0 text-[var(--muted)]"
          />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="start"
          className="z-50 w-72 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-2"
          side="bottom"
          sideOffset={6}
        >
          <Input
            aria-label="搜索项目"
            autoFocus
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索项目"
            value={query}
          />
          <div
            aria-label="授权项目"
            className="mt-2 max-h-72 overflow-y-auto"
            role="listbox"
          >
            {filteredProjects.length ? (
              filteredProjects.map((project) => (
                <button
                  aria-selected={project.id === currentProjectId}
                  className="flex min-h-10 w-full items-center gap-2 rounded-[var(--radius-md)] px-2 text-left text-sm hover:bg-[var(--canvas-soft)]"
                  key={project.id}
                  onClick={() => {
                    onSelect(project.id);
                    setOpen(false);
                    setQuery("");
                  }}
                  role="option"
                  type="button"
                >
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-xs font-semibold text-[var(--primary)]">
                    {project.name.slice(0, 1).toUpperCase()}
                  </span>
                  <span className="min-w-0 flex-1 truncate">
                    {project.name}
                  </span>
                  {project.archived ? (
                    <FolderArchive
                      aria-label="已归档"
                      className="size-3.5 text-[var(--muted)]"
                    />
                  ) : null}
                  {project.id === currentProjectId ? (
                    <Check
                      aria-label="当前项目"
                      className="size-4 text-[var(--primary)]"
                    />
                  ) : null}
                </button>
              ))
            ) : (
              <p className="px-2 py-6 text-center text-sm text-[var(--muted)]">
                没有匹配的项目
              </p>
            )}
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
