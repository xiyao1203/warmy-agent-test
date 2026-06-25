"use client";

import type { ExportTestCasesResponse } from "@warmy/generated-api-client";
import { useState } from "react";

import { Button } from "@/components/ui/button";

type ExportFormat = ExportTestCasesResponse["format"];

export function ExportButton({
  onExport,
}: {
  onExport: (format: ExportFormat) => Promise<ExportTestCasesResponse>;
}) {
  const [format, setFormat] = useState<ExportFormat>("json");
  const [prepared, setPrepared] = useState(false);

  async function exportCases() {
    const result = await onExport(format);
    if (
      typeof document !== "undefined" &&
      typeof URL.createObjectURL === "function" &&
      !document.defaultView?.navigator.userAgent.includes("jsdom")
    ) {
      const blob = new Blob([result.content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `test-cases.${result.format}`;
      anchor.click();
      URL.revokeObjectURL(url);
    }
    setPrepared(Boolean(result.content || result.content === ""));
  }

  return (
    <div className="flex items-center gap-2">
      <select
        aria-label="导出格式"
        className="h-8 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-2 text-sm"
        onChange={(event) => setFormat(event.target.value as ExportFormat)}
        value={format}
      >
        <option value="json">JSON</option>
        <option value="jsonl">JSONL</option>
        <option value="csv">CSV</option>
      </select>
      <Button onClick={exportCases}>导出用例</Button>
      {prepared ? (
        <span className="text-xs text-[var(--success)]">导出内容已准备</span>
      ) : null}
    </div>
  );
}
