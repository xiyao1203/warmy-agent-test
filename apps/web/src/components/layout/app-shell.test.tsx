import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppShell } from "./app-shell";

describe("AppShell", () => {
  it("renders the primary platform navigation", () => {
    render(
      <AppShell projectName="Demo Project" userName="Jason">
        <div>Content</div>
      </AppShell>,
    );

    expect(screen.getByText("Warmy Agent Test")).toBeInTheDocument();
    expect(screen.getByText("测试 Agent")).toBeInTheDocument();
    expect(screen.getByText("运行记录")).toBeInTheDocument();
    expect(screen.getByText("Jason")).toBeInTheDocument();
  });
});
