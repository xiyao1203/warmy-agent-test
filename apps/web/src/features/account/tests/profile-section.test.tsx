import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api", () => ({
  getCurrentUser: vi.fn(),
  updateProfile: vi.fn(),
}));

import { getCurrentUser, updateProfile } from "../api";
import { ProfileSection } from "../profile-section";

const user = {
  id: "user-123456789",
  email: "tester@example.com",
  display_name: "测试用户",
  role: "developer" as const,
  status: "active" as const,
  must_change_password: false,
};

function renderProfile() {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: { retry: false },
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileSection />
    </QueryClientProvider>
  );
}

describe("ProfileSection", () => {
  beforeEach(() => {
    vi.mocked(getCurrentUser).mockReset();
    vi.mocked(updateProfile).mockReset();
    vi.mocked(getCurrentUser).mockResolvedValue(user);
  });

  it("renders a translated identity summary", async () => {
    renderProfile();

    expect(
      await screen.findByRole("heading", { name: "测试用户" })
    ).toBeInTheDocument();
    expect(screen.getAllByText("tester@example.com").length).toBeGreaterThan(0);
    expect(screen.getAllByText("开发").length).toBeGreaterThan(0);
    expect(screen.getAllByText("正常").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: "编辑资料" })
    ).toBeInTheDocument();
  });

  it("can enter and cancel local editing", async () => {
    renderProfile();
    fireEvent.click(await screen.findByRole("button", { name: "编辑资料" }));

    expect(screen.getByLabelText("显示名称")).toHaveValue("测试用户");
    fireEvent.change(screen.getByLabelText("显示名称"), {
      target: { value: "临时名称" },
    });
    fireEvent.click(screen.getByRole("button", { name: "取消" }));

    expect(screen.queryByLabelText("显示名称")).not.toBeInTheDocument();
    expect(updateProfile).not.toHaveBeenCalled();
  });

  it("saves profile changes and surfaces API errors", async () => {
    vi.mocked(updateProfile)
      .mockRejectedValueOnce(new Error("network"))
      .mockResolvedValueOnce({ ...user, display_name: "新名称" });
    renderProfile();
    fireEvent.click(await screen.findByRole("button", { name: "编辑资料" }));
    fireEvent.change(screen.getByLabelText("显示名称"), {
      target: { value: "新名称" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存资料" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "保存失败，请重试"
    );
    fireEvent.click(screen.getByRole("button", { name: "保存资料" }));

    await waitFor(() => {
      expect(screen.queryByLabelText("显示名称")).not.toBeInTheDocument();
    });
    expect(updateProfile).toHaveBeenLastCalledWith(
      {
        display_name: "新名称",
        email: "tester@example.com",
      },
      expect.anything()
    );
  });
});
