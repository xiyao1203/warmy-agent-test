"use client";

import type {
  ImportPreviewError,
  ImportPreviewResponse,
} from "@warmy/generated-api-client";
import { Download, FileJson, FileText, Upload, X } from "lucide-react";
import { useCallback, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

// ── 模板下载 ────────────────────────────────────────────────────────────

const JSON_TEMPLATE = JSON.stringify(
  [
    {
      name: "问候 API 正常响应",
      input: { message: "你好" },
      execution_mode: "api",
      priority: "P1",
      tags: ["smoke"],
    },
  ],
  null,
  2,
);

const JSONL_TEMPLATE =
  '{"name":"问候 API","input":{"message":"你好"},"execution_mode":"api","priority":"P0"}\n';

const CSV_TEMPLATE =
  'name,input,execution_mode,priority,tags\n"问候 API","{""message"":""你好""}",api,P1,"[""smoke""]"\n';

function downloadTemplate(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = ["json", "jsonl", "csv"];

type ImportWizardProps = {
  /** 已发布版本禁止导入 */
  disabled?: boolean;
  /** 导入成功回调，传入实际导入条数 */
  onImport?: (
    content: string,
    format: "json" | "jsonl" | "csv",
  ) => Promise<{ imported_count: number }>;
  /** 预览回调 */
  onPreview?: (
    content: string,
    format: "json" | "jsonl" | "csv",
  ) => Promise<ImportPreviewResponse>;
  /** 导入成功后通知父组件刷新 */
  onSuccess?: (importedCount: number) => void;
};

type WizardStep = "select" | "preview" | "result";

const EXT_ICON_MAP: Record<string, React.ReactNode> = {
  csv: <FileText className="size-4 text-[var(--accent)]" />,
  json: <FileJson className="size-4 text-[var(--accent)]" />,
  jsonl: <FileJson className="size-4 text-[var(--accent)]" />,
};

export function ImportWizard({
  disabled = false,
  onImport,
  onPreview,
  onSuccess,
}: ImportWizardProps) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<WizardStep>("select");
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [importedCount, setImportedCount] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);

  const fileExt = useMemo(() => {
    if (!file) return null;
    return (file.name.split(".").pop()?.toLowerCase() ?? null) as
      | "json"
      | "jsonl"
      | "csv"
      | null;
  }, [file]);

  // ── 选择文件 → 读取内容 → 调用预览 API ───────────────────────────────

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (!selected) return;

      const ext = selected.name.split(".").pop()?.toLowerCase();
      if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
        setError("仅支持 JSON、JSONL、CSV 格式");
        return;
      }
      if (selected.size > MAX_FILE_SIZE) {
        setError("文件不能超过 10MB");
        return;
      }

      setError("");
      setFile(selected);
      setPreview(null);
      setStep("preview");
      setPreviewing(true);

      try {
        const content = await selected.text();
        if (!onPreview) return;
        const result = await onPreview(
          content,
          ext as "json" | "jsonl" | "csv",
        );
        setPreview(result);
      } catch {
        setError("预检失败，请检查文件格式和当前草稿版本。");
      } finally {
        setPreviewing(false);
      }
    },
    [onPreview],
  );

  // ── 确认导入 ──────────────────────────────────────────────────────────

  const handleImport = useCallback(async () => {
    if (!file || !fileExt) return;
    setImporting(true);
    setError("");
    try {
      const content = await file.text();
      if (!onImport) return;
      const result = await onImport(content, fileExt);
      setImportedCount(result.imported_count);
      setStep("result");
      onSuccess?.(result.imported_count);
    } catch {
      setError("导入失败，请检查文件格式后重试。");
    } finally {
      setImporting(false);
    }
  }, [file, fileExt, onImport, onSuccess]);

  // ── 关闭重置 ──────────────────────────────────────────────────────────

  const handleClose = useCallback(() => {
    setOpen(false);
    setStep("select");
    setFile(null);
    setError("");
    setPreview(null);
    setImportedCount(0);
    setImporting(false);
    setPreviewing(false);
  }, []);

  const canImport =
    !importing &&
    preview !== null &&
    preview.valid_count > 0 &&
    preview.errors.length === 0;

  return (
    <Dialog
      onOpenChange={(nextOpen) => {
        if (nextOpen) setOpen(true);
        else handleClose();
      }}
      open={open}
    >
      <DialogTrigger asChild>
        <Button disabled={disabled} variant="ghost">
          <Upload aria-hidden="true" className="mr-1.5 size-4" />
          导入
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogTitle>导入测试用例</DialogTitle>
        <DialogDescription>
          支持 JSON、JSONL、CSV 格式，每次最大 10MB。
          导入前将自动执行预检，存在任意错误时不会写入任何用例。
        </DialogDescription>

        {/* ── Step: select ──────────────────────────────────────────── */}
        {step === "select" && (
          <div className="mt-4 space-y-4">
            <input
              accept=".json,.jsonl,.csv"
              className="hidden"
              onChange={handleFileChange}
              ref={fileRef}
              type="file"
            />
            <div
              className="flex cursor-pointer flex-col items-center gap-2 rounded-[var(--radius-md)] border-2 border-dashed border-[var(--border)] p-8 transition-colors hover:border-[var(--accent)]"
              onClick={() => fileRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ")
                  fileRef.current?.click();
              }}
            >
              <Upload className="size-8 text-[var(--text-muted)]" />
              <p className="text-sm font-medium">点击选择文件</p>
              <p className="text-xs text-[var(--text-muted)]">
                JSON · JSONL · CSV
              </p>
            </div>

            {/* ── 模板下载 ─────────────────────────────────────────── */}
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-subtle)] p-3">
              <p className="mb-2 text-xs font-medium text-[var(--text-muted)]">
                下载模板快速开始
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={() =>
                    downloadTemplate("test-cases.json", JSON_TEMPLATE)
                  }
                  variant="secondary"
                >
                  <Download className="mr-1 size-3.5" />
                  JSON
                </Button>
                <Button
                  onClick={() =>
                    downloadTemplate("test-cases.jsonl", JSONL_TEMPLATE)
                  }
                  variant="secondary"
                >
                  <Download className="mr-1 size-3.5" />
                  JSONL
                </Button>
                <Button
                  onClick={() =>
                    downloadTemplate("test-cases.csv", CSV_TEMPLATE)
                  }
                  variant="secondary"
                >
                  <Download className="mr-1 size-3.5" />
                  CSV
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ── Step: preview ─────────────────────────────────────────── */}
        {step === "preview" && file && (
          <div className="mt-4 space-y-4">
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {fileExt ? EXT_ICON_MAP[fileExt] : null}
                  <span className="text-sm font-medium">{file.name}</span>
                </div>
                <button
                  aria-label="移除文件"
                  className="text-[var(--text-muted)] hover:text-[var(--danger)]"
                  onClick={() => {
                    setFile(null);
                    setStep("select");
                    setError("");
                    setPreview(null);
                  }}
                  type="button"
                >
                  <X className="size-4" />
                </button>
              </div>
              <p className="mt-2 text-xs text-[var(--text-muted)]">
                {formatSize(file.size)} · {fileExt?.toUpperCase()}
              </p>
            </div>

            {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

            {/* ── 预检结果 ─────────────────────────────────────────── */}
            {previewing && (
              <div className="rounded border border-[var(--border)] p-3 text-center text-sm text-[var(--text-muted)]">
                正在预检…
              </div>
            )}

            {preview && (
              <PreviewResult
                errors={preview.errors}
                previewCount={preview.preview.length}
                validCount={preview.valid_count}
              />
            )}

            <div className="flex justify-end gap-2">
              <Button onClick={handleClose} variant="ghost">
                取消
              </Button>
              <Button
                disabled={!canImport}
                loading={importing}
                onClick={handleImport}
                variant="primary"
              >
                确认导入{preview ? `（${preview.valid_count} 条）` : ""}
              </Button>
            </div>
          </div>
        )}

        {/* ── Step: result ──────────────────────────────────────────── */}
        {step === "result" && (
          <div className="mt-4 space-y-4">
            <div className="flex flex-col items-center gap-2 p-6 text-center">
              <CheckCircle className="size-10 text-[var(--success)]" />
              <p className="text-sm font-medium">导入成功</p>
              <p className="text-xs text-[var(--text-muted)]">
                共导入 {importedCount} 条用例{file ? `（${file.name}）` : ""}
              </p>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleClose} variant="primary">
                完成
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ── 预检结果子组件 ─────────────────────────────────────────────────────────

function PreviewResult({
  errors,
  previewCount,
  validCount,
}: {
  errors: ImportPreviewError[];
  previewCount: number;
  validCount: number;
}) {
  const hasErrors = errors.length > 0;

  const errorGroups = useMemo(() => {
    const map = new Map<string, string>();
    for (const e of errors) {
      const key = `${e.line}-${e.field}-${e.code}`;
      if (!map.has(key)) map.set(key, e.message);
    }
    return Array.from(map.entries()).map(([key, message]) => {
      const [line, field, code] = key.split("-");
      return { line: Number(line), field, code, message };
    });
  }, [errors]);

  return (
    <div
      className={`rounded-[var(--radius-md)] border p-4 ${
        hasErrors
          ? "border-[var(--danger)]/30 bg-red-50"
          : "border-[var(--success)]/30 bg-green-50"
      }`}
    >
      <div className="flex items-center gap-2">
        {hasErrors ? (
          <AlertTriangle className="size-4 text-[var(--danger)]" />
        ) : (
          <CheckCircleSmall className="size-4 text-[var(--success)]" />
        )}
        <span className="text-sm font-medium">
          有效 {validCount} / 共 {previewCount} 条
        </span>
      </div>

      {hasErrors && (
        <div className="mt-3 max-h-48 overflow-y-auto space-y-1.5">
          <p className="text-xs font-medium text-[var(--danger)]">
            发现 {errorGroups.length} 个错误：
          </p>
          <ul className="space-y-1">
            {errorGroups.slice(0, 20).map((item, index) => (
              <li
                className="rounded border border-red-200 bg-white px-2 py-1.5 text-xs"
                key={`${item.line}-${item.field}-${index}`}
              >
                <span className="font-mono text-[var(--text-muted)]">
                  第 {item.line} 行 · {item.field}
                </span>
                <span className="ml-1.5 rounded bg-red-100 px-1 font-mono text-[10px] text-red-700">
                  {item.code}
                </span>
                <p className="mt-0.5 text-[var(--danger)]">{item.message}</p>
              </li>
            ))}
            {errors.length > 20 && (
              <li className="text-xs text-[var(--text-muted)]">
                …还有 {errors.length - 20} 个错误未显示
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

// ── 工具函数与图标 ────────────────────────────────────────────────────────

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function CheckCircle(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      fill="none"
      height="24"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      width="24"
      {...props}
    >
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function CheckCircleSmall(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      fill="none"
      height="16"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      width="16"
      {...props}
    >
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function AlertTriangle(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      fill="none"
      height="16"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      width="16"
      {...props}
    >
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" x2="12" y1="9" y2="13" />
      <line x1="12" x2="12.01" y1="17" y2="17" />
    </svg>
  );
}
