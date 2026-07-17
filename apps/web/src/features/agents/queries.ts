import { queryOptions, type QueryClient } from "@tanstack/react-query";

import {
  getAgent,
  getAgentRelationships,
  listAgents,
  listAgentVersions,
} from "./api";

export const agentQueries = {
  all: ["agents"] as const,
  list(projectId: string) {
    return queryOptions({
      queryFn: ({ signal }) => listAgents(projectId, signal),
      queryKey: ["agents", projectId] as const,
    });
  },
  detail(projectId: string, agentId: string) {
    return queryOptions({
      queryFn: ({ signal }) => getAgent(projectId, agentId, signal),
      queryKey: ["agents", projectId, agentId] as const,
    });
  },
  versions(projectId: string, agentId: string) {
    return queryOptions({
      queryFn: ({ signal }) => listAgentVersions(projectId, agentId, signal),
      queryKey: ["agents", projectId, agentId, "versions"] as const,
    });
  },
  relationships(projectId: string, agentId: string) {
    return queryOptions({
      queryFn: ({ signal }) =>
        getAgentRelationships(projectId, agentId, signal),
      queryKey: ["agents", projectId, agentId, "relationships"] as const,
    });
  },
};

export function invalidateAgentList(client: QueryClient, projectId: string) {
  return client.invalidateQueries({
    queryKey: agentQueries.list(projectId).queryKey,
  });
}
