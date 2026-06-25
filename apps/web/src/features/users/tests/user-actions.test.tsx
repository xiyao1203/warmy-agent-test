import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CreateUserDialog } from "../user-dialog";
import { UserDrawer } from "../user-drawer";

describe("CreateUserDialog", () => {
  it("validates required fields and preserves values after a server error", async () => {
    const onCreate = vi.fn().mockRejectedValue(new Error("conflict"));
    render(<CreateUserDialog onCreate={onCreate} />);

    fireEvent.click(screen.getByRole("button", { name: "创建用户" }));
    fireEvent.click(screen.getByRole("button", { name: "保存用户" }));
    expect(await screen.findByText("请输入姓名")).toBeVisible();

    fireEvent.change(screen.getByLabelText("姓名"), {
      target: { value: "开发用户" },
    });
    fireEvent.change(screen.getByLabelText("邮箱"), {
      target: { value: "dev@example.com" },
    });
    fireEvent.change(screen.getByLabelText("初始密码"), {
      target: { value: "Secure-password-123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存用户" }));

    expect(await screen.findByText("创建用户失败，请检查输入后重试。")).toBeVisible();
    expect(screen.getByLabelText("姓名")).toHaveValue("开发用户");
    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
  });
});

describe("UserDrawer actions", () => {
  const currentUser = {
    display_name: "系统管理员",
    email: "admin@example.com",
    id: "admin-1",
    must_change_password: false,
    role: "super_admin" as const,
    status: "active" as const,
  };
  const target = {
    display_name: "开发用户",
    email: "dev@example.com",
    id: "user-2",
    must_change_password: false,
    role: "developer" as const,
    status: "active" as const,
  };

  it("explains session impact before reset and disable", async () => {
    render(
      <UserDrawer
        currentUser={currentUser}
        onOpenChange={vi.fn()}
        onResetPassword={vi.fn()}
        onToggleStatus={vi.fn()}
        open
        user={target}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "重置密码" }));
    expect(
      await screen.findByText(/密码重置会立即撤销该用户的所有有效 Session/),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "取消" }));

    fireEvent.click(screen.getByRole("button", { name: "禁用用户" }));
    expect(
      await screen.findByText(/现有 Session 会立即失效/),
    ).toBeVisible();
  });
});
