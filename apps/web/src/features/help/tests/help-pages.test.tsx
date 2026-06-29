import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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

import DocsPage from "@/app/(help)/docs/page";
import ShortcutsPage from "@/app/(help)/docs/shortcuts/page";
import TestCasesGuidePage from "@/app/(help)/docs/test-cases/page";
import TutorialsPage from "@/app/(help)/docs/tutorials/page";

describe("help content pages", () => {
  it("renders the help landing content without duplicating the shared shell", () => {
    render(<DocsPage />);

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("heading", { name: "帮助中心" })).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "返回应用" })
    ).not.toBeInTheDocument();
    expect(document.querySelector('a[href^="mailto:"]')).toBeNull();
    expect(screen.getByRole("searchbox")).toBeInTheDocument();
  });

  it("renders tutorials as truthful reading resources", () => {
    render(<TutorialsPage />);

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(
      screen.queryByRole("link", { name: "返回应用" })
    ).not.toBeInTheDocument();
    expect(screen.getAllByText("阅读指南")).toHaveLength(6);
    expect(screen.queryByText("🎬")).not.toBeInTheDocument();
  });

  it("renders the test-case guide as one article hierarchy", () => {
    render(<TestCasesGuidePage />);

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(
      screen.queryByRole("link", { name: "返回应用" })
    ).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "先定义测试目标" })).toBeInTheDocument();
  });

  it("renders shortcut groups with semantic keyboard keys", () => {
    const { container } = render(<ShortcutsPage />);

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(
      screen.queryByRole("link", { name: "返回应用" })
    ).not.toBeInTheDocument();
    expect(container.querySelectorAll("kbd").length).toBeGreaterThan(0);
  });
});
