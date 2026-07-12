import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TruncatedText } from "./truncated-text";

describe("TruncatedText", () => {
  it("truncates the visible value and exposes the complete value on hover or focus", () => {
    const value = "一个非常长但必须能够查看完整内容的项目名称";
    render(<TruncatedText>{value}</TruncatedText>);

    const trigger = screen.getByLabelText(value);
    expect(trigger).toHaveClass("truncate");
    expect(trigger).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tooltip")).toHaveAttribute("data-tooltip", value);
    expect(screen.getByRole("tooltip")).toHaveClass(
      "group-focus-within:opacity-100",
    );
  });
});
