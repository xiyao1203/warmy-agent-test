import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button } from "./button";

describe("Button typography", () => {
  it("uses the shared 14px semibold button role", () => {
    render(<Button>新建</Button>);

    expect(screen.getByRole("button", { name: "新建" })).toHaveClass(
      "text-button",
    );
  });
});
