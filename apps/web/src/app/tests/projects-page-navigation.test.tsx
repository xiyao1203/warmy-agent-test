import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ProjectsPage from "../(platform)/projects/page";

const {
  ProjectListScreen,
  push,
  replace,
  useMutation,
  useQuery,
  useQueryClient,
} = vi.hoisted(() => ({
  ProjectListScreen: vi.fn((props: { onOpen: (projectId: string) => void }) => (
    <div data-open-handler={typeof props.onOpen}>项目列表页</div>
  )),
  push: vi.fn(),
  replace: vi.fn(),
  useMutation: vi.fn(() => ({
    isPending: false,
    mutateAsync: vi.fn().mockResolvedValue(undefined),
  })),
  useQuery: vi.fn(),
  useQueryClient: vi.fn(() => ({ invalidateQueries: vi.fn() })),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace }),
}));

vi.mock("@tanstack/react-query", () => ({
  keepPreviousData: (previousData: unknown) => previousData,
  useMutation,
  useQuery,
  useQueryClient,
}));

vi.mock("@/features/projects", () => ({
  ProjectListScreen,
  archiveProject: vi.fn(),
  createProject: vi.fn(),
  listProjectPage: vi.fn(),
  renameProject: vi.fn(),
}));

describe("ProjectsPage navigation", () => {
  it("shows the project list without automatically leaving the page", () => {
    useQuery.mockReturnValue({
      data: {
        items: [{ archived: false, id: "project-1", name: "项目 A" }],
        page: 1,
        page_size: 10,
        total: 1,
        total_pages: 1,
      },
      isError: false,
      isLoading: false,
      isSuccess: true,
    });

    render(<ProjectsPage />);

    expect(screen.getByText("项目列表页")).toBeVisible();
    expect(replace).not.toHaveBeenCalled();

    const props = ProjectListScreen.mock.calls.at(-1)?.[0] as
      | { onOpen: (projectId: string) => void }
      | undefined;
    if (!props) {
      throw new Error("ProjectListScreen was not rendered");
    }

    props.onOpen("project-1");

    expect(push).toHaveBeenCalledWith("/projects/project-1/test-agent");
  });
});
