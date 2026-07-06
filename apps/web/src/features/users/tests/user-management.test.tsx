import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { UserManagement } from "../user-management";

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

describe("UserManagement", () => {
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
});
