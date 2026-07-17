"use client";

import { FolderKanban, LoaderCircle } from "lucide-react";

export function ProjectEmptyVisual() {
  return (
    <div
      aria-hidden="true"
      className="grid size-14 place-items-center rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--canvas-soft)] text-[var(--primary)]"
      data-testid="project-empty-visual"
      data-visual-kind="project-empty-glyph"
      data-visual-source="warmy-product-system"
    >
      <FolderKanban className="size-6" />
    </div>
  );
}

export function ProjectLoadingMotion() {
  return (
    <div
      className="inline-flex items-center gap-2 py-4 text-sm text-[var(--muted)]"
      data-motion-source="warmy-product-system"
      data-testid="project-loading-motion"
      role="status"
    >
      <LoaderCircle
        aria-hidden="true"
        className="size-4 animate-spin text-[var(--primary)]"
      />
      <span>正在加载项目...</span>
    </div>
  );
}
