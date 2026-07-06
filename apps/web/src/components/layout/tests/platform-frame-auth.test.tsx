import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { PlatformFrame } from "../platform-frame";

const { AppShell, getCurrentUser, listProjects, push, replace } = vi.hoisted(
  () => ({
    AppShell: vi.fn(({ children }: { children: ReactNode }) => <>{children}</>),
    getCurrentUser: vi.fn(),
    listProjects: vi.fn(),
    push: vi.fn(),
    replace: vi.fn(),
  }),
);

const user = {
  display_name: "开发用户",
  email: "dev@example.com",
  id: "user-1",
  must_change_password: false,
  role: "developer",
  status: "active",
};

const project = { archived: false, id: "project-1", name: "项目 A" };

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects",
  useRouter: () => ({ push, replace }),
}));

vi.mock("@/features/auth", () => ({ getCurrentUser }));
vi.mock("@/features/projects", () => ({ listProjects }));
vi.mock("../app-shell", () => ({ AppShell }));

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

  it("opens the test agent when switching projects", async () => {
    getCurrentUser.mockResolvedValueOnce(user);
    listProjects.mockResolvedValueOnce([project]);
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={client}>
        <PlatformFrame>workspace</PlatformFrame>
      </QueryClientProvider>,
    );

    await waitFor(() => expect(AppShell).toHaveBeenCalled());
    const props = AppShell.mock.calls.at(-1)?.[0] as
      | { onProjectSelect: (projectId: string) => void }
      | undefined;
    if (!props) {
      throw new Error("AppShell was not rendered");
    }
    props.onProjectSelect("project-2");

    expect(push).toHaveBeenCalledWith("/projects/project-2/test-agent");
  });
});
