import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Badge } from "./badge";

describe("Badge typography", () => {
  it("uses the shared caption role for status text", () => {
    render(<Badge tone="success">已启用</Badge>);

    expect(screen.getByText("已启用")).toHaveClass("text-badge");
  });
});
