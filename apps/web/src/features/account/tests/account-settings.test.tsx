import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api", () => ({
  changePassword: vi.fn(),
  getUserSettings: vi.fn(),
  updateUserSettings: vi.fn(),
}));

import { getUserSettings } from "../api";
import { NotificationsSection } from "../notifications-section";
import { PreferencesSection } from "../preferences-section";
import { SecuritySection } from "../security-section";

const settings = {
  theme: "dark" as const,
  language: "en" as const,
  email_notifications: false,
  push_notifications: true,
  test_complete_notifications: false,
};

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: { retry: false },
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("account settings sections", () => {
  beforeEach(() => {
    vi.mocked(getUserSettings).mockReset();
    vi.mocked(getUserSettings).mockResolvedValue(settings);
  });

  it("reflects preferences returned asynchronously by the server", async () => {
    renderWithQueryClient(<PreferencesSection />);

    expect(await screen.findByRole("button", { name: "深色" })).toHaveAttribute(
      "aria-pressed",
      "true"
    );
    expect(screen.getByRole("button", { name: "English" })).toHaveAttribute(
      "aria-pressed",
      "true"
    );
  });

  it("preserves accessible notification switch states", async () => {
    renderWithQueryClient(<NotificationsSection />);

    expect(await screen.findByRole("switch", { name: "邮件通知" })).toHaveAttribute(
      "aria-checked",
      "false"
    );
    expect(screen.getByRole("switch", { name: "推送通知" })).toHaveAttribute(
      "aria-checked",
      "true"
    );
  });

  it("does not expose unsupported destructive account actions", () => {
    renderWithQueryClient(<SecuritySection />);

    expect(screen.getByText("暂未开放")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "删除账户" })
    ).not.toBeInTheDocument();
  });
});
