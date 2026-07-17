"use client";

import { Download, FileJson, FileText, FileCode } from "lucide-react";
import { useState } from "react";

import { CONTROL_API_URL } from "@/lib/api/base-url";

type ReportFormat = "json" | "junit" | "html";

type ReportDownloadButtonProps = {
  projectId: string;
  runId: string;
};

const REPORT_OPTIONS: Array<{
  format: ReportFormat;
  label: string;
  description: string;
  icon: typeof FileJson;
}> = [
  {
    format: "json",
    label: "JSON",
    description: "标准化测试结果格式",
    icon: FileJson,
  },
  {
    format: "junit",
    label: "JUnit XML",
    description: "CI/CD 集成格式",
    icon: FileCode,
  },
  {
    format: "html",
    label: "HTML",
    description: "人类可读报告",
    icon: FileText,
  },
];

export function ReportDownloadButton({
  projectId,
  runId,
}: ReportDownloadButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [downloading, setDownloading] = useState<ReportFormat | null>(null);

  const handleDownload = async (format: ReportFormat) => {
    setDownloading(format);
    try {
      // raw-fetch-allowed: streamed report download preserves response headers and Blob body
      const response = await fetch(
        `${CONTROL_API_URL}/api/v1/projects/${projectId}/runs/${runId}/export?format=${format}`,
        {
          credentials: "include",
        },
      );

      if (!response.ok) {
        throw new Error(`下载失败: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `run-${runId}-report.${format === "junit" ? "xml" : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("报告下载失败:", error);
      alert("报告下载失败，请稍后重试");
    } finally {
      setDownloading(null);
      setIsOpen(false);
    }
  };

  return (
    <div className="relative">
      <button
        className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 py-2 text-sm font-medium transition-colors hover:bg-[var(--canvas-soft)]"
        onClick={() => setIsOpen(!isOpen)}
        type="button"
      >
        <Download className="size-4" />
        下载报告
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-2">
            <p className="px-2 pb-2 text-xs font-medium text-[var(--muted)]">
              选择报告格式
            </p>
            <div className="space-y-1">
              {REPORT_OPTIONS.map((option) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.format}
                    className="flex w-full items-center gap-3 rounded-[var(--radius-md)] px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--canvas-soft)] disabled:opacity-50"
                    disabled={downloading !== null}
                    onClick={() => handleDownload(option.format)}
                    type="button"
                  >
                    <Icon className="size-4 shrink-0 text-[var(--muted)]" />
                    <div className="min-w-0 flex-1">
                      <p className="font-medium">{option.label}</p>
                      <p className="text-xs text-[var(--muted)]">
                        {option.description}
                      </p>
                    </div>
                    {downloading === option.format && (
                      <div className="size-4 animate-spin rounded-full border-2 border-[var(--primary)] border-t-transparent" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
