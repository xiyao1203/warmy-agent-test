import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const { searchParamsState } = vi.hoisted(() => ({
  searchParamsState: { value: "section=profile" },
}));

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(searchParamsState.value),
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

import { AccountCenter } from "../account-center";
import { normalizeAccountSection } from "../types";

describe("AccountCenter", () => {
  it("renders the account center title", () => {
    render(
      <AccountCenter>
        <div>Test content</div>
      </AccountCenter>,
    );

    expect(screen.getByText("账户中心")).toBeInTheDocument();
    expect(
      screen.getByText("管理您的个人信息、偏好设置和安全选项"),
    ).toBeInTheDocument();
  });

  it("renders all navigation sections", () => {
    render(
      <AccountCenter>
        <div>Test content</div>
      </AccountCenter>,
    );

    expect(screen.getAllByRole("link", { name: /个人资料/ })).toHaveLength(2);
    expect(screen.getAllByRole("link", { name: /偏好设置/ })).toHaveLength(2);
    expect(screen.getAllByRole("link", { name: /通知设置/ })).toHaveLength(2);
    expect(screen.getAllByRole("link", { name: /账号安全/ })).toHaveLength(2);
  });

  it("renders children content", () => {
    render(
      <AccountCenter>
        <div data-testid="child-content">Test content</div>
      </AccountCenter>,
    );

    expect(screen.getByTestId("child-content")).toBeInTheDocument();
  });

  it("falls back to profile when the section query is invalid", () => {
    searchParamsState.value = "section=unknown";

    render(
      <AccountCenter>
        <div>Test content</div>
      </AccountCenter>,
    );

    for (const link of screen.getAllByRole("link", { name: /个人资料/ })) {
      expect(link).toHaveAttribute("aria-current", "page");
    }
  });

  it("normalizes known and unknown account sections", () => {
    expect(normalizeAccountSection("security")).toBe("security");
    expect(normalizeAccountSection("unknown")).toBe("profile");
    expect(normalizeAccountSection(null)).toBe("profile");
  });
});
