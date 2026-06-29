import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  usePathname: () => "/docs/tutorials",
}));

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

import { HelpShell } from "../help-shell";

describe("HelpShell", () => {
  it("marks the current help destination and renders shared actions", () => {
    render(
      <HelpShell>
        <p>教程内容</p>
      </HelpShell>,
    );

    expect(screen.getByRole("link", { name: "返回应用" })).toHaveAttribute(
      "href",
      "/projects",
    );
    expect(screen.getByRole("link", { name: "提交反馈" })).toHaveAttribute(
      "href",
      "/feedback",
    );
    expect(screen.getByText("教程内容")).toBeInTheDocument();

    const desktopNavigation = screen.getByRole("navigation", {
      name: "帮助中心目录",
    });
    expect(
      within(desktopNavigation).getByRole("link", { name: "教程" }),
    ).toHaveAttribute("aria-current", "page");
    expect(within(desktopNavigation).getAllByRole("link")).toHaveLength(6);
  });
});
