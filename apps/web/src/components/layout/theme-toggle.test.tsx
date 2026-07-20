import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeToggle } from "./theme-toggle";

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
    document.documentElement.style.colorScheme = "";
  });

  it("toggles immediately without opening a theme menu", async () => {
    localStorage.setItem("theme", "light");
    render(<ThemeToggle />);

    const lightButton = screen.getByRole("button", { name: "切换至深色" });
    expect(lightButton).not.toHaveAttribute("title");
    expect(lightButton.querySelector(".lucide-sun")).toBeInTheDocument();
    expect(lightButton.querySelector(".theme-toggle-icon")).toBeInTheDocument();
    expect(screen.getByRole("tooltip")).toHaveAttribute(
      "data-tooltip",
      "切换至深色",
    );

    fireEvent.click(lightButton);

    await waitFor(() => expect(localStorage.getItem("theme")).toBe("dark"));
    const darkButton = screen.getByRole("button", { name: "切换至浅色" });
    expect(darkButton.querySelector(".lucide-moon")).toBeInTheDocument();
    expect(document.documentElement).toHaveClass("dark");
    expect(document.documentElement.style.colorScheme).toBe("dark");
    expect(screen.getByRole("tooltip")).toHaveAttribute(
      "data-tooltip",
      "切换至浅色",
    );
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    expect(screen.queryByRole("menuitemradio")).not.toBeInTheDocument();
  });

  it("migrates a legacy system preference once without subscribing to changes", async () => {
    const addEventListener = vi.fn();
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockImplementation(() => ({
        addEventListener,
        matches: true,
        media: "(prefers-color-scheme: dark)",
        removeEventListener: vi.fn(),
      })),
    });
    localStorage.setItem("theme", "system");
    render(<ThemeToggle />);

    await waitFor(() => expect(localStorage.getItem("theme")).toBe("dark"));
    expect(document.documentElement).toHaveClass("dark");
    expect(document.documentElement).toHaveAttribute(
      "data-theme-preference",
      "dark",
    );
    expect(addEventListener).not.toHaveBeenCalled();
  });
});
