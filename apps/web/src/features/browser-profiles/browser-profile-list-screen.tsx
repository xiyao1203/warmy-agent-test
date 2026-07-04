"use client";

import { useQuery } from "@tanstack/react-query";

import {
  completeBrowserProfileLogin,
  createBrowserProfile,
  deleteBrowserProfile,
  listBrowserProfiles,
  startBrowserProfile,
  stopBrowserProfile,
  updateBrowserProfile,
} from "./api";
import { BrowserProfileList } from "./browser-profile-list";

export function BrowserProfileListScreen({ projectId }: { projectId: string }) {
  const query = useQuery({
    queryFn: () => listBrowserProfiles(projectId),
    queryKey: ["browser-profiles", projectId],
  });

  if (query.isPending) {
    return <BrowserProfileList loading projectId={projectId} />;
  }
  if (query.isError) {
    return <BrowserProfileList error="service" projectId={projectId} />;
  }

  async function refresh() {
    await query.refetch();
  }

  return (
    <BrowserProfileList
      profiles={query.data ?? []}
      projectId={projectId}
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
    />
  );
}
