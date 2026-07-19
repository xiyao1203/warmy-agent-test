import { queryOptions, type QueryClient } from "@tanstack/react-query";

import {
  getAgent,
  getAgentRelationships,
  listAgents,
  listAgentVersions,
} from "./api";

export const agentQueries = {
  all: ["agents"] as const,
  list(projectId: string, page = 1, pageSize = 10) {
    return queryOptions({
      queryFn: ({ signal }) => listAgents(projectId, signal, page, pageSize),
      queryKey: ["agents", projectId, page, pageSize] as const,
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
    queryKey: ["agents", projectId],
  });
}
