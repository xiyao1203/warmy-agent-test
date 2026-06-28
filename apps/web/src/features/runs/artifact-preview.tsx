"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type Artifact = {
  id: string;
  name: string;
  type: "image" | "video" | "file";
  url: string;
  size: number;
  created_at: string;
};

type ArtifactPreviewProps = {
  artifacts: Artifact[];
  onArtifactSelect?: (artifact: Artifact) => void;
};

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(0)) + " " + sizes[i];
}

function getArtifactTypeLabel(type: Artifact["type"]): string {
  switch (type) {
    case "image":
      return "图片";
    case "video":
      return "视频";
    case "file":
      return "文件";
  }
}

function getArtifactTypeBadgeTone(type: Artifact["type"]): "accent" | "success" | "neutral" {
  switch (type) {
    case "image":
      return "accent";
    case "video":
      return "success";
    case "file":
      return "neutral";
  }
}

export function ArtifactPreview({ artifacts, onArtifactSelect }: ArtifactPreviewProps) {
  const [selectedType, setSelectedType] = useState<"all" | Artifact["type"]>("all");

  const filteredArtifacts = artifacts.filter((artifact) => {
    if (selectedType === "all") return true;
    return artifact.type === selectedType;
  });

  const handleDownload = (artifact: Artifact, e: React.MouseEvent) => {
    e.stopPropagation();
    // 创建一个临时的 a 标签来触发下载
    const link = document.createElement("a");
    link.href = artifact.url;
    link.download = artifact.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (artifacts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-[var(--radius-md)] border border-dashed border-[var(--border)] p-8">
        <p className="text-sm text-[var(--text-muted)]">暂无产物文件</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 头部统计和筛选 */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--text-muted)]">共 {artifacts.length} 个产物文件</p>
        <div className="flex gap-2">
          <Button
            variant={selectedType === "all" ? "primary" : "secondary"}
            onClick={() => setSelectedType("all")}
          >
            全部
          </Button>
          <Button
            variant={selectedType === "image" ? "primary" : "secondary"}
            onClick={() => setSelectedType("image")}
          >
            图片
          </Button>
          <Button
            variant={selectedType === "video" ? "primary" : "secondary"}
            onClick={() => setSelectedType("video")}
          >
            视频
          </Button>
          <Button
            variant={selectedType === "file" ? "primary" : "secondary"}
            onClick={() => setSelectedType("file")}
          >
            文件
          </Button>
        </div>
      </div>

      {/* 产物列表 */}
      <div className="space-y-2">
        {filteredArtifacts.map((artifact) => (
          <div
            key={artifact.id}
            className="flex cursor-pointer items-center justify-between rounded-[var(--radius-md)] border border-[var(--border)] p-3 transition-colors hover:bg-[var(--surface-hover)]"
            onClick={() => onArtifactSelect?.(artifact)}
          >
            <div className="flex items-center gap-3">
              {/* 文件图标 */}
              <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-sm)] bg-[var(--surface-subtle)]">
                {artifact.type === "image" && (
                  <svg
                    className="h-5 w-5 text-[var(--text-muted)]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                )}
                {artifact.type === "video" && (
                  <svg
                    className="h-5 w-5 text-[var(--text-muted)]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                )}
                {artifact.type === "file" && (
                  <svg
                    className="h-5 w-5 text-[var(--text-muted)]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                )}
              </div>

              {/* 文件信息 */}
              <div>
                <p className="text-sm font-medium">{artifact.name}</p>
                <p className="text-xs text-[var(--text-muted)]">
                  {formatFileSize(artifact.size)} · {new Date(artifact.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* 类型徽章 */}
              <Badge tone={getArtifactTypeBadgeTone(artifact.type)}>
                {getArtifactTypeLabel(artifact.type)}
              </Badge>

              {/* 下载按钮 */}
              <Button
                variant="secondary"
                onClick={(e) => handleDownload(artifact, e)}
              >
                下载
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}