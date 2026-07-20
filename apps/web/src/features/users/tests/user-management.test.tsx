import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserManagement } from "../user-management";
import { UserManagementScreen } from "../user-management-screen";

const {
  createUser,
  deleteUser,
  getCurrentUser,
  listUsers,
  resetUserPassword,
  setUserEnabled,
  updateUser,
} = vi.hoisted(() => ({
  createUser: vi.fn(),
  deleteUser: vi.fn(),
  getCurrentUser: vi.fn(),
  listUsers: vi.fn(),
  resetUserPassword: vi.fn(),
  setUserEnabled: vi.fn(),
  updateUser: vi.fn(),
}));

vi.mock("@/features/auth", () => ({ getCurrentUser }));
vi.mock("../api", () => ({
  createUser,
  deleteUser,
  listUsers,
  resetUserPassword,
  setUserEnabled,
  updateUser,
}));

const currentUser = {
  display_name: "系统管理员",
  email: "admin@example.com",
  id: "admin-1",
  must_change_password: false,
  role: "super_admin" as const,
  status: "active" as const,
};

const users = [
  currentUser,
  {
    display_name: "开发用户",
    email: "dev@example.com",
    id: "user-2",
    must_change_password: true,
    role: "developer" as const,
    status: "disabled" as const,
  },
];

function renderUserManagementScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={client}>
      <UserManagementScreen />
    </QueryClientProvider>,
  );
}

describe("UserManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState({}, "", "/system/users?page=1&page_size=10");
  });

  it("renders loading, error and permission states", () => {
    const { rerender } = render(
      <UserManagement currentUser={currentUser} loading />,
    );
    expect(screen.getByText("正在加载用户…")).toBeVisible();

    rerender(<UserManagement currentUser={currentUser} error="service" />);
    expect(screen.getByText("用户列表暂时不可用")).toBeVisible();

    rerender(<UserManagement currentUser={currentUser} error="permission" />);
    expect(screen.getByText("你没有用户管理权限")).toBeVisible();
  });

  it("renders empty and no-search-results states", () => {
    const { rerender } = render(
      <UserManagement currentUser={currentUser} users={[]} />,
    );
    expect(screen.getByText("暂无用户")).toBeVisible();

    rerender(<UserManagement currentUser={currentUser} users={users} />);
    fireEvent.change(screen.getByPlaceholderText("搜索姓名或邮箱"), {
      target: { value: "nobody" },
    });
    expect(screen.getByText("没有匹配的用户")).toBeVisible();
  });

  it("renders dense rows and opens a protected detail drawer", async () => {
    render(<UserManagement currentUser={currentUser} users={users} />);

    expect(screen.getByText("dev@example.com")).toBeVisible();
    expect(screen.getAllByText("开发").length).toBeGreaterThan(0);
    expect(screen.getAllByText("已禁用").length).toBeGreaterThan(0);
    expect(screen.getAllByText("需改密").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: /查看系统管理员/ }));
    expect(await screen.findByRole("dialog")).toBeVisible();
    expect(screen.getByText("当前登录账号")).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "禁用用户" }),
    ).not.toBeInTheDocument();
  });

  it("keeps search and filters on one desktop row", () => {
    render(<UserManagement currentUser={currentUser} users={users} />);

    expect(screen.getByTestId("user-filter-bar")).toHaveClass(
      "flex",
      "items-center",
      "gap-3",
    );
    expect(screen.getByRole("button", { name: "全部角色" })).toHaveClass(
      "basis-40",
      "shrink-0",
    );
    expect(screen.getByRole("button", { name: "全部状态" })).toHaveClass(
      "basis-40",
      "shrink-0",
    );
  });

  it("requests the next numbered page from the pagination control", async () => {
    const onPageChange = vi.fn();
    render(
      <UserManagement
        currentUser={currentUser}
        onPageChange={onPageChange}
        page={1}
        pageSize={10}
        total={12}
        totalPages={2}
        users={users}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "下一页" }));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("replaces rows with the requested user page in the screen data flow", async () => {
    const nextPageUser = {
      display_name: "审核用户",
      email: "reviewer@example.com",
      id: "user-3",
      must_change_password: false,
      role: "reviewer" as const,
      status: "active" as const,
    };
    getCurrentUser.mockResolvedValue(currentUser);
    listUsers.mockImplementation(async (page: number) => {
      if (page === 1) {
        return {
          items: users,
          next_cursor: null,
          page: 1,
          page_size: 10,
          total: 11,
          total_pages: 2,
        };
      }
      return {
        items: [nextPageUser],
        next_cursor: null,
        page: 2,
        page_size: 10,
        total: 11,
        total_pages: 2,
      };
    });

    renderUserManagementScreen();

    expect(await screen.findByText("dev@example.com")).toBeVisible();
    expect(screen.queryByText("reviewer@example.com")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "下一页" }));

    expect(await screen.findByText("reviewer@example.com")).toBeVisible();
    await waitFor(() => expect(listUsers).toHaveBeenCalledWith(2, 10));
    expect(screen.queryByText("dev@example.com")).not.toBeInTheDocument();
  });
});
