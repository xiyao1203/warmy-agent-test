import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginScreen } from "../login-screen";

const router = vi.hoisted(() => ({
  push: vi.fn(),
  replace: vi.fn(),
}));
const getCurrentUserMock = vi.hoisted(() => vi.fn());
const loginMock = vi.hoisted(() => vi.fn());
const listProjectsMock = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

vi.mock("../api", () => ({
  getCurrentUser: getCurrentUserMock,
  login: loginMock,
}));

vi.mock("@/features/projects", () => ({
  listProjects: listProjectsMock,
}));

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: { retry: false },
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("LoginScreen", () => {
  beforeEach(() => {
    router.push.mockClear();
    router.replace.mockClear();
    getCurrentUserMock.mockReset();
    loginMock.mockReset();
    listProjectsMock.mockReset();
    getCurrentUserMock.mockRejectedValue(new Error("unauthenticated"));
  });

  it("renders the product landing page and opens login dialog", async () => {
    renderWithQueryClient(<LoginScreen />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Warmy Agent Test" }),
    ).toBeVisible();
    const brand = screen.getByTestId("landing-brand");
    const brandMark = brand.querySelector("[data-brand-mark]");

    expect(brandMark).toHaveAttribute("data-brand-mark", "agent-test-glyph");
    expect(brandMark).toHaveAttribute(
      "data-brand-mark-source",
      "warmy-product-system",
    );
    expect(screen.getByRole("link", { name: "查看运行证据" })).toHaveAttribute(
      "href",
      "#product-evidence",
    );
    expect(screen.getByRole("region", { name: "真实运行证据" })).toBeVisible();
    expect(
      screen.queryByText(/不展示桌面壳|减少用户理解成本/),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("PROJECT")).not.toBeInTheDocument();
    expect(screen.getByText(/持续验证 Agent 的能力、质量与安全/)).toBeVisible();
    expect(screen.getByRole("button", { name: "外观设置" })).toBeVisible();
    expect(
      screen.queryByRole("navigation", { name: "产品导航" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Test Agent")).not.toBeInTheDocument();
    expect(screen.queryByText("Cases")).not.toBeInTheDocument();
    expect(screen.queryByText("Runs")).not.toBeInTheDocument();
    expect(screen.queryByText("Gates")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "搜索" }),
    ).not.toBeInTheDocument();

    fireEvent.click(await screen.findByRole("button", { name: "登录" }));

    expect(screen.getByRole("dialog")).toBeVisible();
    expect(screen.getByText("登录测试工作台")).toBeVisible();
    expect(screen.getByLabelText("邮箱")).toBeVisible();
    expect(screen.getByText(/会话受保护/)).toBeVisible();
  });

  it("keeps users on the landing page after login until they click the workspace entry", async () => {
    loginMock.mockResolvedValue({
      display_name: "Jason",
      email: "jason@example.com",
      id: "user-1",
      must_change_password: false,
      role: "super_admin",
      status: "active",
    });
    listProjectsMock.mockResolvedValue([
      { archived: false, id: "project-1", name: "测试项目" },
    ]);

    renderWithQueryClient(<LoginScreen />);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "登录并开始" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "登录并开始" }));

    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("邮箱"), {
      target: { value: "jason@example.com" },
    });
    fireEvent.change(within(dialog).getByLabelText("密码"), {
      target: { value: "correct-password" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "登录" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(router.replace).not.toHaveBeenCalled();
    expect(router.push).not.toHaveBeenCalled();
    expect(
      screen.getByRole("heading", { level: 1, name: "Warmy Agent Test" }),
    ).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));

    expect(router.push).toHaveBeenCalledWith("/projects/project-1/test-agent");
  });

  it("shows a workbench entry instead of login when an existing session is still valid", async () => {
    getCurrentUserMock.mockResolvedValue({
      display_name: "Jason",
      email: "jason@example.com",
      id: "user-1",
      must_change_password: false,
      role: "super_admin",
      status: "active",
    });
    listProjectsMock.mockResolvedValue([
      { archived: false, id: "project-1", name: "测试项目" },
    ]);

    renderWithQueryClient(<LoginScreen />);

    const workbenchButton = await screen.findByRole("button", {
      name: "工作台",
    });
    await waitFor(() => expect(workbenchButton).toBeEnabled());

    fireEvent.click(workbenchButton);

    expect(router.push).toHaveBeenCalledWith("/projects/project-1/test-agent");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("does not show login while the existing session check is still pending", () => {
    getCurrentUserMock.mockReturnValue(new Promise(() => undefined));

    renderWithQueryClient(<LoginScreen />);

    expect(
      screen.queryByRole("button", { name: "登录" }),
    ).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "正在检查" })).toEqual(
      expect.arrayContaining([expect.any(HTMLButtonElement)]),
    );
    for (const button of screen.getAllByRole("button", { name: "正在检查" })) {
      expect(button).toBeDisabled();
    }
  });
});
