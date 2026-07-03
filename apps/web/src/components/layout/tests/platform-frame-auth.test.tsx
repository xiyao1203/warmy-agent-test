import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { PlatformFrame } from "../platform-frame";

const { getCurrentUser, listProjects, replace } = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  listProjects: vi.fn(),
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects",
  useRouter: () => ({ push: vi.fn(), replace }),
}));

vi.mock("@/features/auth", () => ({ getCurrentUser }));
vi.mock("@/features/projects", () => ({ listProjects }));
vi.mock("../app-shell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

describe("PlatformFrame authentication", () => {
  it("redirects an unauthenticated visitor even while the project query is disabled", async () => {
    getCurrentUser.mockRejectedValueOnce(new Error("unauthenticated"));
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={client}>
        <PlatformFrame>workspace</PlatformFrame>
      </QueryClientProvider>,
    );

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith("/login?returnTo=%2Fprojects"),
    );
    expect(listProjects).not.toHaveBeenCalled();
  });
});
