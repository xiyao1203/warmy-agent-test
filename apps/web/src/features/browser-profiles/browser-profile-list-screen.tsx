"use client";

import { useQuery } from "@tanstack/react-query";

import {
  createBrowserProfile,
  deleteBrowserProfile,
  listBrowserProfiles,
  updateBrowserProfile,
} from "./api";
import { BrowserProfileList } from "./browser-profile-list";

export function BrowserProfileListScreen({ projectId }: { projectId: string }) {
  const query = useQuery({
    queryFn: () => listBrowserProfiles(projectId),
    queryKey: ["browser-profiles", projectId],
  });

  if (query.isPending) {
    return <BrowserProfileList loading />;
  }
  if (query.isError) {
    return <BrowserProfileList error="service" />;
  }

  async function refresh() {
    await query.refetch();
  }

  return (
    <BrowserProfileList
      profiles={query.data ?? []}
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
    />
  );
}
