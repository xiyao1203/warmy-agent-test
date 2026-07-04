"use client";

import type { ImportTestCasesRequest } from "@warmy/generated-api-client";
import { Download } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import {
  buildTestCaseTemplate,
  TEST_CASE_FIELD_HELP,
  TEST_CASE_REQUIRED_FIELD_LABELS,
  testCaseTemplateFilename,
  type TestCaseImportFormat,
} from "./test-case-format";

type ImportLineError = { line: number; reason: string };

function downloadTemplate(format: TestCaseImportFormat) {
  const blob = new Blob([buildTestCaseTemplate(format)], {
    type: "text/plain;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = testCaseTemplateFilename(format);
  a.click();
  URL.revokeObjectURL(url);
}

export function ImportDialog({
  onImport,
}: {
  onImport: (payload: ImportTestCasesRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [format, setFormat] =
    useState<ImportTestCasesRequest["format"]>("json");
  const [content, setContent] = useState("");
  const [errors, setErrors] = useState<ImportLineError[]>([]);
  const [message, setMessage] = useState("");

  async function submit() {
    setErrors([]);
    setMessage("");
    try {
      await onImport({ content, format });
      setOpen(false);
    } catch (error) {
      const problem = error as { errors?: ImportLineError[] };
      if (problem.errors?.length) {
        setErrors(problem.errors);
      } else {
        setMessage("导入失败，请检查格式和内容。");
      }
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button>导入用例</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>导入测试用例</DialogTitle>
        <DialogDescription>
          支持 JSON、JSONL 和
          CSV；任一行错误时不会写入部分数据。字段与“新增测试用例”保持一致。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <div className="rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-xs font-medium text-[var(--ink)]">
                  中文导入模板
                </p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  必填：{TEST_CASE_REQUIRED_FIELD_LABELS.join("、")}
                </p>
              </div>
              <div className="flex gap-2">
                {(["json", "jsonl", "csv"] as const).map((item) => (
                  <Button
                    key={item}
                    onClick={() => downloadTemplate(item)}
                    variant="secondary"
                  >
                    <Download className="mr-1 size-3.5" />
                    {item.toUpperCase()}
                  </Button>
                ))}
              </div>
            </div>
            <ul className="mt-2 space-y-1 text-xs text-[var(--muted)]">
              {TEST_CASE_FIELD_HELP.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <label className="block text-sm font-medium">
            导入格式
            <DropdownSelect
              className="mt-1.5 h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
              onChange={(event) =>
                setFormat(
                  event.target.value as ImportTestCasesRequest["format"],
                )
              }
              value={format}
            >
              <option value="json">JSON</option>
              <option value="jsonl">JSONL</option>
              <option value="csv">CSV</option>
            </DropdownSelect>
          </label>
          <label className="block text-sm font-medium">
            导入内容
            <textarea
              aria-label="导入内容"
              className="mt-1.5 min-h-48 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 py-2 font-mono text-xs"
              onChange={(event) => setContent(event.target.value)}
              value={content}
            />
          </label>
          {errors.length ? (
            <ul className="space-y-1 rounded-[var(--radius-md)] bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]">
              {errors.map((error) => (
                <li key={`${error.line}-${error.reason}`}>
                  第 {error.line} 行：{error.reason}
                </li>
              ))}
            </ul>
          ) : null}
          {message ? (
            <p className="text-sm text-[var(--danger)]">{message}</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button onClick={submit} variant="primary">
              开始导入
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
