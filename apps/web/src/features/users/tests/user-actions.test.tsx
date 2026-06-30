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

    expect(
      await screen.findByText("创建用户失败，请检查输入后重试。"),
    ).toBeVisible();
    expect(screen.getByLabelText("姓名")).toHaveValue("开发用户");
    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
  });
});

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

describe("UserDrawer actions", () => {
  it("explains session impact before reset and disable", async () => {
    render(
      <UserDrawer
        currentUser={currentUser}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
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
    expect(await screen.findByText(/现有 Session 会立即失效/)).toBeVisible();
  });

  it("opens edit form with current user values", async () => {
    const onEdit = vi.fn().mockResolvedValue(undefined);
    render(
      <UserDrawer
        currentUser={currentUser}
        onDelete={vi.fn()}
        onEdit={onEdit}
        onOpenChange={vi.fn()}
        onResetPassword={vi.fn()}
        onToggleStatus={vi.fn()}
        open
        user={target}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "编辑用户" }));
    expect(
      await screen.findByRole("heading", { name: "编辑用户" }),
    ).toBeVisible();
    expect(screen.getByLabelText("姓名")).toHaveValue("开发用户");
    expect(screen.getByLabelText("邮箱")).toHaveValue("dev@example.com");
  });

  it("submits edit and calls onEdit with user id", async () => {
    const onEdit = vi.fn().mockResolvedValue(undefined);
    render(
      <UserDrawer
        currentUser={currentUser}
        onDelete={vi.fn()}
        onEdit={onEdit}
        onOpenChange={vi.fn()}
        onResetPassword={vi.fn()}
        onToggleStatus={vi.fn()}
        open
        user={target}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "编辑用户" }));
    fireEvent.change(screen.getByLabelText("姓名"), {
      target: { value: "开发用户2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存修改" }));

    await waitFor(() => expect(onEdit).toHaveBeenCalledTimes(1));
    expect(onEdit).toHaveBeenCalledWith(
      "user-2",
      expect.objectContaining({ display_name: "开发用户2" }),
    );
  });

  it("shows delete confirmation with impact text", async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined);
    render(
      <UserDrawer
        currentUser={currentUser}
        onDelete={onDelete}
        onEdit={vi.fn()}
        onOpenChange={vi.fn()}
        onResetPassword={vi.fn()}
        onToggleStatus={vi.fn()}
        open
        user={target}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "删除用户" }));
    expect(await screen.findByText(/删除后该用户将无法登录/)).toBeVisible();
    expect(screen.getByText(/此操作不可撤销/)).toBeVisible();
  });

  it("confirms delete and calls onDelete", async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined);
    render(
      <UserDrawer
        currentUser={currentUser}
        onDelete={onDelete}
        onEdit={vi.fn()}
        onOpenChange={vi.fn()}
        onResetPassword={vi.fn()}
        onToggleStatus={vi.fn()}
        open
        user={target}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "删除用户" }));
    fireEvent.click(screen.getByRole("button", { name: "确认删除用户" }));

    await waitFor(() => expect(onDelete).toHaveBeenCalledTimes(1));
    expect(onDelete).toHaveBeenCalledWith("user-2");
  });

  it("hides edit, disable and delete for current user", () => {
    render(
      <UserDrawer
        currentUser={currentUser}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
        onOpenChange={vi.fn()}
        onResetPassword={vi.fn()}
        onToggleStatus={vi.fn()}
        open
        user={currentUser}
      />,
    );

    expect(screen.getByText("编辑用户")).toBeVisible();
    expect(screen.queryByText("禁用用户")).not.toBeInTheDocument();
    expect(screen.queryByText("删除用户")).not.toBeInTheDocument();
    expect(screen.getByText(/当前账号不能在此禁用或降权/)).toBeVisible();
  });
});
