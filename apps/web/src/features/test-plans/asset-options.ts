import { listAgentVersions, listAgents } from "@/features/agents";
import { listDatasets, listDatasetVersions } from "@/features/datasets";
import { listGates, listGateRuns } from "@/features/gates";
import { listScorers } from "@/features/scorers";

import { listEnvironmentTemplates } from "./api";
import type { VersionAssetOption } from "./test-plan-version-dialog";

export interface TestPlanAssetOptions {
  agentVersions: VersionAssetOption[];
  datasetVersions: VersionAssetOption[];
  environments: VersionAssetOption[];
  gates: VersionAssetOption[];
  runs: VersionAssetOption[];
  scorers: VersionAssetOption[];
}

export async function loadTestPlanAssetOptions(
  projectId: string,
  signal?: AbortSignal,
): Promise<TestPlanAssetOptions> {
  const [agentPage, datasetPage, environments, scorers, gates, runs] =
    await Promise.all([
      listAgents(projectId, signal),
      listDatasets(projectId, signal),
      listEnvironmentTemplates(projectId, signal),
      listScorers(projectId, signal),
      listGates(projectId, signal),
      listGateRuns(projectId, signal),
    ]);
  const agentVersions = (
    await Promise.all(
      agentPage.items.map(async (agent) =>
        (await listAgentVersions(projectId, agent.id, signal)).map(
          (version) => ({
            id: version.id,
            label: `${agent.name} v${version.version_number}`,
            status: version.status,
          }),
        ),
      ),
    )
  ).flat();
  const datasetVersions = (
    await Promise.all(
      datasetPage.items.map(async (dataset) =>
        (await listDatasetVersions(projectId, dataset.id, signal)).map(
          (version) => ({
            id: version.id,
            label: `${dataset.name} v${version.version_number}`,
            status: version.status,
          }),
        ),
      ),
    )
  ).flat();
  return {
    agentVersions,
    datasetVersions,
    environments: environments.map((template) => ({
      id: template.id,
      label: template.name,
    })),
    scorers: scorers
      .filter((scorer) => scorer.enabled && scorer.latest_published_version_id)
      .map((scorer) => ({
        id: String(scorer.latest_published_version_id),
        label: `${scorer.name} v${scorer.latest_published_version_number ?? 1}`,
      })),
    gates: gates.map((gate) => ({ id: gate.id, label: gate.name })),
    runs: runs.map((run) => ({
      id: run.id,
      label: `${run.status} · ${new Date(run.created_at).toLocaleString("zh-CN")}`,
    })),
  };
}
