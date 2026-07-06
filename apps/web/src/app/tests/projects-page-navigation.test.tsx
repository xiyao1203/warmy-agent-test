import { render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ProjectsPage from "../(platform)/projects/page";

const { replace, useMutation, useQuery } = vi.hoisted(() => ({
  replace: vi.fn(),
  useMutation: vi.fn(() => ({ isPending: false, mutate: vi.fn() })),
  useQuery: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation,
  useQuery,
}));

vi.mock("@/features/projects", () => ({
  createProject: vi.fn(),
  listProjects: vi.fn(),
}));

describe("ProjectsPage navigation", () => {
  it("opens the test agent for the first project", async () => {
    useQuery.mockReturnValue({
      data: [{ archived: false, id: "project-1", name: "项目 A" }],
      isLoading: false,
      isSuccess: true,
    });

    render(<ProjectsPage />);

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith("/projects/project-1/test-agent"),
    );
  });
});
