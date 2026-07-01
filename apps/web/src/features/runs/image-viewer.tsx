"use client";

import { useState } from "react";
import Image from "next/image";

import { Button } from "@/components/ui/button";

type ImageViewerProps = {
  src: string;
  alt: string;
  onFullscreen?: () => void;
};

export function ImageViewer({ src, alt, onFullscreen }: ImageViewerProps) {
  const [scale, setScale] = useState(1);

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.5, 3));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.5, 0.5));
  };

  const handleReset = () => {
    setScale(1);
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center gap-2">
        <Button variant="secondary" onClick={handleZoomOut}>
          -
        </Button>
        <span className="min-w-[60px] text-center text-sm font-medium">
          {Math.round(scale * 100)}%
        </span>
        <Button variant="secondary" onClick={handleZoomIn}>
          +
        </Button>
        <Button variant="secondary" onClick={handleReset}>
          重置
        </Button>
        {onFullscreen && (
          <Button variant="primary" onClick={onFullscreen}>
            全屏
          </Button>
        )}
      </div>

      {/* 图片容器 */}
      <div className="flex items-center justify-center overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--canvas-soft)]">
        <Image
          src={src}
          alt={alt}
          height={800}
          unoptimized
          width={1200}
          style={{ transform: `scale(${scale})` }}
          className="max-h-[500px] max-w-full object-contain transition-transform"
        />
      </div>
    </div>
  );
}
