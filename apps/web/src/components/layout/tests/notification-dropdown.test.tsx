import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

import { NotificationDropdown } from "../notification-dropdown";

describe("NotificationDropdown", () => {
  it("renders the notification bell icon", () => {
    render(<NotificationDropdown />);

    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("shows dropdown when clicking the bell icon", () => {
    render(<NotificationDropdown />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(screen.getByText("通知中心")).toBeInTheDocument();
  });

  it("shows empty state when no notifications", () => {
    render(<NotificationDropdown />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(screen.getByText("暂无新通知")).toBeInTheDocument();
  });

  it("shows link to notification settings", () => {
    render(<NotificationDropdown />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    const settingsLink = screen.getByText("通知偏好设置");
    expect(settingsLink).toBeInTheDocument();
    expect(settingsLink.closest("a")).toHaveAttribute("href", "/account?section=notifications");
  });
});
