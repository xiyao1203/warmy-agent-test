import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { VideoPlayer } from "../video-player";

describe("VideoPlayer", () => {
  const defaultProps = {
    src: "https://example.com/video.mp4",
  };

  it("renders video element with src", () => {
    render(<VideoPlayer {...defaultProps} />);
    
    const video = document.querySelector("video");
    expect(video).toBeInTheDocument();
    expect(video).toHaveAttribute("src", defaultProps.src);
  });

  it("shows play button", () => {
    render(<VideoPlayer {...defaultProps} />);
    
    expect(screen.getByText("播放")).toBeInTheDocument();
  });

  it("toggles between play and pause button", () => {
    render(<VideoPlayer {...defaultProps} />);
    
    const playButton = screen.getByText("播放");
    fireEvent.click(playButton);
    
    expect(screen.getByText("暂停")).toBeInTheDocument();
  });

  it("shows download button", () => {
    render(<VideoPlayer {...defaultProps} />);
    
    expect(screen.getByText("下载")).toBeInTheDocument();
  });

  it("calls onDownload when download button is clicked", () => {
    const mockOnDownload = vi.fn();
    render(<VideoPlayer {...defaultProps} onDownload={mockOnDownload} />);
    
    fireEvent.click(screen.getByText("下载"));
    expect(mockOnDownload).toHaveBeenCalled();
  });

  it("shows volume button", () => {
    render(<VideoPlayer {...defaultProps} />);
    
    expect(screen.getByText("音量")).toBeInTheDocument();
  });

  it("toggles mute when volume button is clicked", () => {
    render(<VideoPlayer {...defaultProps} />);
    
    fireEvent.click(screen.getByText("音量"));
    
    // 点击后应该显示静音图标或文本
    expect(screen.getByText("静音")).toBeInTheDocument();
  });

  it("shows video duration", () => {
    render(<VideoPlayer {...defaultProps} />);
    
    // 应该显示时间格式
    expect(screen.getByText("0:00 / 0:00")).toBeInTheDocument();
  });
});