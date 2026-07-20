"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { usePaginationState } from "@/lib/use-pagination-state";

import {
  completeBrowserProfileLogin,
  createBrowserProfile,
  deleteBrowserProfile,
  startBrowserProfile,
  stopBrowserProfile,
  updateBrowserProfile,
  verifyBrowserProfile,
} from "./api";
import { BrowserProfileList } from "./browser-profile-list";
import { browserProfileQueries, invalidateBrowserProfileList } from "./queries";

export function BrowserProfileListScreen({ projectId }: { projectId: string }) {
  const pagination = usePaginationState();
  const query = useQuery(
    browserProfileQueries.list(projectId, pagination.page, pagination.pageSize),
  );
  const queryClient = useQueryClient();

  if (query.isPending) {
    return <BrowserProfileList loading projectId={projectId} />;
  }
  if (query.isError) {
    return <BrowserProfileList error="service" projectId={projectId} />;
  }

  async function refresh() {
    await invalidateBrowserProfileList(queryClient, projectId);
  }

  return (
    <BrowserProfileList
      onPageChange={pagination.setPage}
      onPageSizeChange={pagination.setPageSize}
      page={query.data.page ?? pagination.page}
      pageSize={pagination.pageSize}
      profiles={query.data.items}
      projectId={projectId}
      total={query.data.total}
      totalPages={query.data.total_pages}
      onCreate={async (payload) => {
        const result = await createBrowserProfile(projectId, payload);
        await refresh();
        return result;
      }}
      onUpdate={async (profileId, payload) => {
        const result = await updateBrowserProfile(
          projectId,
          profileId,
          payload,
        );
        await refresh();
        return result;
      }}
      onDelete={async (profileId) => {
        await deleteBrowserProfile(projectId, profileId);
        await refresh();
      }}
      onStart={async (profileId, payload) => {
        const result = await startBrowserProfile(projectId, profileId, payload);
        await refresh();
        return result;
      }}
      onCompleteLogin={async (profileId, payload) => {
        const result = await completeBrowserProfileLogin(
          projectId,
          profileId,
          payload,
        );
        await refresh();
        return result;
      }}
      onStop={async (profileId) => {
        const result = await stopBrowserProfile(projectId, profileId);
        await refresh();
        return result;
      }}
      onVerify={async (profileId) => {
        const result = await verifyBrowserProfile(projectId, profileId);
        await refresh();
        return result;
      }}
    />
  );
}
