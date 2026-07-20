import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const pageTitleFiles = [
  "features/account/account-center.tsx",
  "features/agents/agent-detail.tsx",
  "features/agents/agent-list.tsx",
  "features/browser-profiles/browser-profile-list.tsx",
  "features/datasets/dataset-detail.tsx",
  "features/datasets/dataset-list.tsx",
  "features/environments/environment-list.tsx",
  "features/experiments/experiment-list.tsx",
  "features/gates/gate-list.tsx",
  "features/model-configs/model-config-list.tsx",
  "features/projects/project-list-screen.tsx",
  "features/projects/project-overview.tsx",
  "features/reviews/review-workbench.tsx",
  "features/runs/run-center.tsx",
  "features/runs/run-detail.tsx",
  "features/scorers/scorer-list.tsx",
  "features/security/security-scan.tsx",
  "features/test-plans/test-plan-detail.tsx",
  "features/test-plans/test-plan-list.tsx",
  "features/users/user-management.tsx",
] as const;

const technicalSurfaceFiles = [
  "components/uiverse/chat/markdown-content.tsx",
  "features/agents/agent-version-advanced-sections.tsx",
  "features/agents/agent-version-sections.tsx",
  "features/agents/connection-test-panel.tsx",
  "features/agents/version-detail-drawer.tsx",
  "features/datasets/import-dialog.tsx",
  "features/datasets/test-case-detail.tsx",
  "features/datasets/test-case-editor.tsx",
  "features/datasets/test-case-step-editor.tsx",
  "features/runs/run-detail.tsx",
  "features/runs/run-result-workbench.tsx",
  "features/test-agent/context-panel.tsx",
] as const;

function source(file: string) {
  return readFileSync(resolve(process.cwd(), "src", file), "utf8");
}

describe("typography architecture", () => {
  it("uses the page-title role on every primary workspace screen", () => {
    for (const file of pageTitleFiles) {
      expect(source(file), file).toMatch(
        /<h1[^>]*className="[^"]*text-page-title/,
      );
    }
  });

  it("uses the code role on core Prompt, JSON, Trace, and log surfaces", () => {
    for (const file of technicalSurfaceFiles) {
      expect(source(file), file).toContain("text-code");
    }
  });
});
