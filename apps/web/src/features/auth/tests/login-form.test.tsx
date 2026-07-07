import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "../login-form";

const user = {
  display_name: "Jason",
  email: "jason@example.com",
  id: "user-1",
  must_change_password: false,
  role: "super_admin" as const,
  status: "active" as const,
};

const projects = [
  { archived: false, id: "project-1", name: "测试项目" },
  { archived: true, id: "project-2", name: "归档项目" },
];

describe("LoginForm", () => {
  it("validates email and password before submitting", async () => {
    const onLogin = vi.fn();
    render(<LoginForm onLogin={onLogin} onSuccess={vi.fn()} returnTo="/" />);

    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(await screen.findByText("请输入有效的邮箱地址")).toBeVisible();
    expect(screen.getByText("请输入密码")).toBeVisible();
    expect(onLogin).not.toHaveBeenCalled();
  });

  it("shows one generic message for authentication failure", async () => {
    const onLogin = vi.fn().mockRejectedValue(new Error("account missing"));
    render(<LoginForm onLogin={onLogin} onSuccess={vi.fn()} returnTo="/" />);

    fireEvent.change(screen.getByLabelText("邮箱"), {
      target: { value: "jason@example.com" },
    });
    fireEvent.change(screen.getByLabelText("密码"), {
      target: { value: "wrong-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(await screen.findByText("邮箱或密码不正确，请重试。")).toBeVisible();
    expect(screen.queryByText("account missing")).not.toBeInTheDocument();
  });

  it("prevents repeated submission and returns to the intended path", async () => {
    let resolveLogin!: (value: typeof user) => void;
    const onLogin = vi.fn(
      () =>
        new Promise<typeof user>((resolve) => {
          resolveLogin = resolve;
        }),
    );
    const onSuccess = vi.fn();
    render(
      <LoginForm
        onLogin={onLogin}
        onSuccess={onSuccess}
        returnTo="/projects/project-1/overview"
      />,
    );

    fireEvent.change(screen.getByLabelText("邮箱"), {
      target: { value: "jason@example.com" },
    });
    fireEvent.change(screen.getByLabelText("密码"), {
      target: { value: "correct-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(screen.getByRole("button", { name: "正在登录…" })).toBeDisabled();
    expect(onLogin).toHaveBeenCalledTimes(1);

    resolveLogin(user);
    await waitFor(() =>
      expect(onSuccess).toHaveBeenCalledWith("/projects/project-1/overview"),
    );
  });

  it("opens the first project test agent by default after landing page login", async () => {
    const onLogin = vi.fn().mockResolvedValue(user);
    const onListProjects = vi.fn().mockResolvedValue(projects);
    const onSuccess = vi.fn();
    render(
      <LoginForm
        onListProjects={onListProjects}
        onLogin={onLogin}
        onSuccess={onSuccess}
      />,
    );

    fireEvent.change(screen.getByLabelText("邮箱"), {
      target: { value: "jason@example.com" },
    });
    fireEvent.change(screen.getByLabelText("密码"), {
      target: { value: "correct-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    await waitFor(() =>
      expect(onSuccess).toHaveBeenCalledWith("/projects/project-1/test-agent"),
    );
    expect(onListProjects).toHaveBeenCalledTimes(1);
  });

  it("still opens the first project test agent when the account requires a password change", async () => {
    const onLogin = vi
      .fn()
      .mockResolvedValue({ ...user, must_change_password: true });
    const onListProjects = vi.fn().mockResolvedValue(projects);
    const onSuccess = vi.fn();
    render(
      <LoginForm
        onListProjects={onListProjects}
        onLogin={onLogin}
        onSuccess={onSuccess}
      />,
    );

    fireEvent.change(screen.getByLabelText("邮箱"), {
      target: { value: "jason@example.com" },
    });
    fireEvent.change(screen.getByLabelText("密码"), {
      target: { value: "correct-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    await waitFor(() =>
      expect(onSuccess).toHaveBeenCalledWith("/projects/project-1/test-agent"),
    );
  });

  it("ignores stale account return paths and opens the test agent", async () => {
    const onLogin = vi.fn().mockResolvedValue(user);
    const onListProjects = vi.fn().mockResolvedValue(projects);
    const onSuccess = vi.fn();
    render(
      <LoginForm
        onListProjects={onListProjects}
        onLogin={onLogin}
        onSuccess={onSuccess}
        returnTo="/account?section=security"
      />,
    );

    fireEvent.change(screen.getByLabelText("邮箱"), {
      target: { value: "jason@example.com" },
    });
    fireEvent.change(screen.getByLabelText("密码"), {
      target: { value: "correct-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    await waitFor(() =>
      expect(onSuccess).toHaveBeenCalledWith("/projects/project-1/test-agent"),
    );
  });
});
