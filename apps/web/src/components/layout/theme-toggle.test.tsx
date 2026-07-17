import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeToggle } from "./theme-toggle";

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
    document.documentElement.style.colorScheme = "";
  });

  it("offers light, dark, and system choices and persists the preference", () => {
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
    expect(
      screen.getByRole("menuitemradio", { name: "跟随系统" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("menuitemradio", { name: "深色" }));
    expect(localStorage.getItem("theme")).toBe("dark");
    expect(document.documentElement).toHaveClass("dark");
    expect(document.documentElement.style.colorScheme).toBe("dark");
  });

  it("reacts to system theme changes while system mode is selected", () => {
    const listeners: Array<(event: MediaQueryListEvent) => void> = [];
    let matches = false;
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockImplementation(() => ({
        addEventListener: (
          _: string,
          listener: (event: MediaQueryListEvent) => void,
        ) => listeners.push(listener),
        get matches() {
          return matches;
        },
        media: "(prefers-color-scheme: dark)",
        removeEventListener: vi.fn(),
      })),
    });
    localStorage.setItem("theme", "system");
    render(<ThemeToggle />);

    expect(document.documentElement).toHaveClass("light");
    matches = true;
    listeners.forEach((listener) =>
      listener({ matches: true } as MediaQueryListEvent),
    );
    expect(document.documentElement).toHaveClass("dark");
  });
});
