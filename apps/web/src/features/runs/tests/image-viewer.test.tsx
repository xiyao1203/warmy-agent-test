import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ImageViewer } from "../image-viewer";

describe("ImageViewer", () => {
  const defaultProps = {
    src: "https://example.com/image.png",
    alt: "Test image",
  };

  it("renders image with src and alt", () => {
    render(<ImageViewer {...defaultProps} />);

    const img = screen.getByRole("img");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", defaultProps.src);
    expect(img).toHaveAttribute("alt", defaultProps.alt);
  });

  it("shows zoom in button", () => {
    render(<ImageViewer {...defaultProps} />);

    expect(screen.getByText("+")).toBeInTheDocument();
  });

  it("shows zoom out button", () => {
    render(<ImageViewer {...defaultProps} />);

    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("shows fullscreen button when onFullscreen is provided", () => {
    const mockOnFullscreen = vi.fn();
    render(<ImageViewer {...defaultProps} onFullscreen={mockOnFullscreen} />);

    expect(screen.getByText("全屏")).toBeInTheDocument();
  });

  it("does not show fullscreen button when onFullscreen is not provided", () => {
    render(<ImageViewer {...defaultProps} />);

    expect(screen.queryByText("全屏")).not.toBeInTheDocument();
  });

  it("shows reset zoom button", () => {
    render(<ImageViewer {...defaultProps} />);

    expect(screen.getByText("重置")).toBeInTheDocument();
  });

  it("increases scale when zoom in is clicked", () => {
    render(<ImageViewer {...defaultProps} />);

    fireEvent.click(screen.getByText("+"));

    // 图片应该放大
    const img = screen.getByRole("img");
    expect(img).toHaveStyle({ transform: "scale(1.5)" });
  });

  it("decreases scale when zoom out is clicked", () => {
    render(<ImageViewer {...defaultProps} />);

    fireEvent.click(screen.getByText("-"));

    // 图片应该缩小
    const img = screen.getByRole("img");
    expect(img).toHaveStyle({ transform: "scale(0.5)" });
  });

  it("resets zoom when reset is clicked", () => {
    render(<ImageViewer {...defaultProps} />);

    // 先放大
    fireEvent.click(screen.getByText("+"));
    fireEvent.click(screen.getByText("+"));

    // 然后重置
    fireEvent.click(screen.getByText("重置"));

    const img = screen.getByRole("img");
    expect(img).toHaveStyle({ transform: "scale(1)" });
  });

  it("calls onFullscreen when fullscreen button is clicked", () => {
    const mockOnFullscreen = vi.fn();
    render(<ImageViewer {...defaultProps} onFullscreen={mockOnFullscreen} />);

    fireEvent.click(screen.getByText("全屏"));
    expect(mockOnFullscreen).toHaveBeenCalled();
  });

  it("shows zoom level indicator", () => {
    render(<ImageViewer {...defaultProps} />);

    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("updates zoom level after zoom in", () => {
    render(<ImageViewer {...defaultProps} />);

    fireEvent.click(screen.getByText("+"));
    expect(screen.getByText("150%")).toBeInTheDocument();
  });
});
