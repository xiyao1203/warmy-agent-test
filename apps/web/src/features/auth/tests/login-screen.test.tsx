import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LoginScreen } from "../login-screen";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: vi.fn(),
  }),
}));

describe("LoginScreen", () => {
  it("renders the product landing page and opens login dialog", () => {
    render(<LoginScreen />);

    expect(screen.getAllByText("Warmy Agent Test").length).toBeGreaterThan(0);
    expect(screen.getByText("Agent 发布前的测试证据层")).toBeVisible();
    expect(screen.getByText("Release readiness")).toBeVisible();
    expect(screen.getByText("发布前证据链")).toBeVisible();
    expect(screen.queryByText("PROJECT")).not.toBeInTheDocument();
    expect(screen.getByText(/把 AI Agent 的每次变更/)).toBeVisible();
    expect(
      screen.getByRole("button", { name: /切换到(暗色|亮色)模式/ }),
    ).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(screen.getByRole("dialog")).toBeVisible();
    expect(screen.getByText("登录测试工作台")).toBeVisible();
    expect(screen.getByLabelText("邮箱")).toBeVisible();
    expect(screen.getByText(/会话受保护/)).toBeVisible();
  });
});
