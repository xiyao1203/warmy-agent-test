import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeToggle } from "./theme-toggle";

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
    document.documentElement.style.colorScheme = "";
  });

  it("offers only light and dark choices and persists the preference", () => {
    render(<ThemeToggle />);
    fireEvent.pointerDown(screen.getByRole("button", { name: "外观设置" }), {
      button: 0,
      ctrlKey: false,
    });

    expect(
      screen.getByRole("menuitemradio", { name: "浅色" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("menuitemradio", { name: "深色" }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("menuitemradio")).toHaveLength(2);
    expect(
      screen.queryByRole("menuitemradio", { name: "跟随系统" }),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("menuitemradio", { name: "深色" }));
    expect(localStorage.getItem("theme")).toBe("dark");
    expect(document.documentElement).toHaveClass("dark");
    expect(document.documentElement.style.colorScheme).toBe("dark");
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
