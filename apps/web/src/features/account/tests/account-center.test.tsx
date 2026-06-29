import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("section=profile"),
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

import { AccountCenter } from "../account-center";

describe("AccountCenter", () => {
  it("renders the account center title", () => {
    render(
      <AccountCenter>
        <div>Test content</div>
      </AccountCenter>
    );

    expect(screen.getByText("账户中心")).toBeInTheDocument();
    expect(screen.getByText("管理您的个人信息、偏好设置和安全选项")).toBeInTheDocument();
  });

  it("renders all navigation sections", () => {
    render(
      <AccountCenter>
        <div>Test content</div>
      </AccountCenter>
    );

    expect(screen.getByText("个人资料")).toBeInTheDocument();
    expect(screen.getByText("偏好设置")).toBeInTheDocument();
    expect(screen.getByText("通知设置")).toBeInTheDocument();
    expect(screen.getByText("账号安全")).toBeInTheDocument();
  });

  it("renders children content", () => {
    render(
      <AccountCenter>
        <div data-testid="child-content">Test content</div>
      </AccountCenter>
    );

    expect(screen.getByTestId("child-content")).toBeInTheDocument();
  });
});
