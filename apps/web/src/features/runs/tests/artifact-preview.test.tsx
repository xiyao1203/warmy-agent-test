import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ArtifactPreview } from "../artifact-preview";

describe("ArtifactPreview", () => {
  const mockArtifacts = [
    {
      id: "artifact-1",
      name: "screenshot.png",
      type: "image" as const,
      url: "https://example.com/screenshot.png",
      size: 1024,
      created_at: "2026-06-29T10:00:00Z",
    },
    {
      id: "artifact-2",
      name: "recording.mp4",
      type: "video" as const,
      url: "https://example.com/recording.mp4",
      size: 5 * 1024 * 1024,
      created_at: "2026-06-29T10:01:00Z",
    },
    {
      id: "artifact-3",
      name: "data.json",
      type: "file" as const,
      url: "https://example.com/data.json",
      size: 2048,
      created_at: "2026-06-29T10:02:00Z",
    },
  ];

  it("renders artifact list with file icons", () => {
    render(<ArtifactPreview artifacts={mockArtifacts} />);

    expect(screen.getByText("screenshot.png")).toBeInTheDocument();
    expect(screen.getByText("recording.mp4")).toBeInTheDocument();
    expect(screen.getByText("data.json")).toBeInTheDocument();
  });

  it("shows file size for each artifact", () => {
    render(<ArtifactPreview artifacts={mockArtifacts} />);

    // 使用 getByTextContent 来匹配包含文件大小的元素
    const sizeElements = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("1 KB") || false;
    });
    expect(sizeElements.length).toBeGreaterThanOrEqual(1);

    const sizeElements2 = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("5 MB") || false;
    });
    expect(sizeElements2.length).toBeGreaterThanOrEqual(1);

    const sizeElements3 = screen.getAllByText((content, element) => {
      return element?.textContent?.includes("2 KB") || false;
    });
    expect(sizeElements3.length).toBeGreaterThanOrEqual(1);
  });

  it("displays artifact type badges", () => {
    render(<ArtifactPreview artifacts={mockArtifacts} />);

    // 使用 getAllByText 因为 "图片" 可能出现在筛选按钮和徽章中
    const imageBadges = screen.getAllByText("图片");
    expect(imageBadges.length).toBeGreaterThanOrEqual(1);

    const videoBadges = screen.getAllByText("视频");
    expect(videoBadges.length).toBeGreaterThanOrEqual(1);

    const fileBadges = screen.getAllByText("文件");
    expect(fileBadges.length).toBeGreaterThanOrEqual(1);
  });

  it("calls onArtifactSelect when artifact is clicked", () => {
    const mockOnSelect = vi.fn();
    render(
      <ArtifactPreview
        artifacts={mockArtifacts}
        onArtifactSelect={mockOnSelect}
      />,
    );

    fireEvent.click(screen.getByText("screenshot.png"));
    expect(mockOnSelect).toHaveBeenCalledWith(mockArtifacts[0]);
  });

  it("shows download button for each artifact", () => {
    render(<ArtifactPreview artifacts={mockArtifacts} />);

    const downloadButtons = screen.getAllByText("下载");
    expect(downloadButtons).toHaveLength(3);
  });

  it("renders empty state when no artifacts", () => {
    render(<ArtifactPreview artifacts={[]} />);

    expect(screen.getByText("暂无产物文件")).toBeInTheDocument();
  });

  it("shows artifact count", () => {
    render(<ArtifactPreview artifacts={mockArtifacts} />);

    expect(screen.getByText("共 3 个产物文件")).toBeInTheDocument();
  });

  it("filters artifacts by type", () => {
    render(<ArtifactPreview artifacts={mockArtifacts} />);

    // 点击图片筛选按钮（找到 button 元素）
    const imageButtons = screen.getAllByText("图片");
    const imageButton = imageButtons.find((el) => el.tagName === "BUTTON");
    expect(imageButton).toBeDefined();
    fireEvent.click(imageButton!);
    expect(screen.getByText("screenshot.png")).toBeInTheDocument();
    expect(screen.queryByText("recording.mp4")).not.toBeInTheDocument();
    expect(screen.queryByText("data.json")).not.toBeInTheDocument();

    // 点击全部筛选
    fireEvent.click(screen.getByText("全部"));
    expect(screen.getByText("screenshot.png")).toBeInTheDocument();
    expect(screen.getByText("recording.mp4")).toBeInTheDocument();
    expect(screen.getByText("data.json")).toBeInTheDocument();
  });
});
