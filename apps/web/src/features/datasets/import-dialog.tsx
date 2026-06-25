"use client";

import type { ImportTestCasesRequest } from "@warmy/generated-api-client";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

type ImportLineError = { line: number; reason: string };

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
          支持 JSON、JSONL 和 CSV；任一行错误时不会写入部分数据。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            导入格式
            <select
              className="mt-1.5 h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3"
              onChange={(event) =>
                setFormat(event.target.value as ImportTestCasesRequest["format"])
              }
              value={format}
            >
              <option value="json">JSON</option>
              <option value="jsonl">JSONL</option>
              <option value="csv">CSV</option>
            </select>
          </label>
          <label className="block text-sm font-medium">
            导入内容
            <textarea
              aria-label="导入内容"
              className="mt-1.5 min-h-48 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 font-mono text-xs"
              onChange={(event) => setContent(event.target.value)}
              value={content}
            />
          </label>
          {errors.length ? (
            <ul className="space-y-1 rounded-[var(--radius-sm)] bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]">
              {errors.map((error) => (
                <li key={`${error.line}-${error.reason}`}>
                  第 {error.line} 行：{error.reason}
                </li>
              ))}
            </ul>
          ) : null}
          {message ? <p className="text-sm text-[var(--danger)]">{message}</p> : null}
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
