"use client";

import { FileJson, FileText, Upload, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

type ImportWizardProps = {
  datasetId?: string;
  projectId?: string;
  versionId?: string;
  onImport?: (file: File) => Promise<unknown>;
  onPreview?: (file: File) => Promise<{
    valid_count: number;
    errors: Array<{ line: number; field: string; message: string }>;
  }>;
  onSuccess?: () => void;
};

type WizardStep = "select" | "preview" | "result";

export function ImportWizard({
  onImport,
  onPreview,
  onSuccess,
}: ImportWizardProps) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<WizardStep>("select");
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<{
    valid_count: number;
    errors: Array<{ line: number; field: string; message: string }>;
  } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (!selected) return;

      const ext = selected.name.split(".").pop()?.toLowerCase();
      if (!["json", "jsonl", "csv"].includes(ext || "")) {
        setError("仅支持 JSON、JSONL、CSV 格式");
        return;
      }
      if (selected.size > 10 * 1024 * 1024) {
        setError("文件不能超过 10MB");
        return;
      }

      setError("");
      setFile(selected);
      setStep("preview");
      setPreview(null);
      if (onPreview) {
        try {
          setPreview(await onPreview(selected));
        } catch {
          setError("预检失败，请检查文件格式和当前草稿版本。");
        }
      }
    },
    [onPreview],
  );

  const handleImport = useCallback(async () => {
    if (!file || !onImport) return;
    setImporting(true);
    setError("");
    setPreview(null);
    try {
      await onImport(file);
      setStep("result");
      onSuccess?.();
    } catch {
      setError("导入失败，请检查文件格式后重试。");
    } finally {
      setImporting(false);
    }
  }, [file, onImport, onSuccess]);

  const handleClose = useCallback(() => {
    setOpen(false);
    setStep("select");
    setFile(null);
    setError("");
    setImporting(false);
  }, []);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <Dialog
      onOpenChange={(nextOpen) => {
        if (nextOpen) setOpen(true);
        else handleClose();
      }}
      open={open}
    >
      <DialogTrigger asChild>
        <Button variant="ghost">
          <Upload aria-hidden="true" className="mr-1.5 size-4" />
          导入
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogTitle>导入测试用例</DialogTitle>
        <DialogDescription>
          支持 JSON、JSONL、CSV 格式，每次最大 10MB。
        </DialogDescription>

        {/* Step: select */}
        {step === "select" && (
          <div className="mt-4 space-y-3">
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
            >
              <Upload className="size-8 text-[var(--text-muted)]" />
              <p className="text-sm font-medium">点击选择文件</p>
            </div>
            <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
              <span className="flex items-center gap-1">
                <FileJson className="size-3.5" /> JSON
              </span>
              <span className="flex items-center gap-1">
                <FileJson className="size-3.5" /> JSONL
              </span>
              <span className="flex items-center gap-1">
                <FileText className="size-3.5" /> CSV
              </span>
            </div>
          </div>
        )}

        {/* step: preview */}
        {step === "preview" && file && (
          <div className="mt-4 space-y-4">
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileJson className="size-4 text-[var(--accent)]" />
                  <span className="text-sm font-medium">{file.name}</span>
                </div>
                <button
                  aria-label="移除文件"
                  className="text-[var(--text-muted)] hover:text-[var(--danger)]"
                  onClick={() => {
                    setFile(null);
                    setStep("select");
                    setError("");
                  }}
                >
                  <X className="size-4" />
                </button>
              </div>
              <p className="mt-2 text-xs text-[var(--text-muted)]">
                {formatSize(file.size)} · {file.type || "未知格式"}
              </p>
            </div>
            {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
            {preview && (
              <div className="rounded border border-[var(--border)] p-3 text-sm">
                <p>有效用例：{preview.valid_count} 条</p>
                {preview.errors.length > 0 && (
                  <ul className="mt-2 space-y-1 text-xs text-[var(--danger)]">
                    {preview.errors.slice(0, 10).map((item, index) => (
                      <li key={`${item.line}-${item.field}-${index}`}>
                        第 {item.line} 行 · {item.field}：{item.message}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button onClick={handleClose}>取消</Button>
              <Button
                disabled={importing || !preview || preview.errors.length > 0}
                loading={importing}
                onClick={handleImport}
                variant="primary"
              >
                确认导入
              </Button>
            </div>
          </div>
        )}

        {/* step: result */}
        {step === "result" && (
          <div className="mt-4 space-y-4">
            <div className="flex flex-col items-center gap-2 p-6 text-center">
              <CheckCircle className="size-10 text-[var(--success)]" />
              <p className="text-sm font-medium">导入成功</p>
              <p className="text-xs text-[var(--text-muted)]">
                文件 {file?.name} 已导入完成。
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
