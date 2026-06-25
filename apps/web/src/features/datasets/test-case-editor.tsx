"use client";

import type {
  CreateTestCaseRequest,
  TestCaseResponse,
} from "@warmy/generated-api-client";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export function TestCaseEditor({
  caseItem,
  onSubmit,
  triggerLabel,
}: {
  caseItem?: TestCaseResponse;
  onSubmit: (payload: CreateTestCaseRequest) => Promise<unknown>;
  triggerLabel: string;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(caseItem?.name ?? "");
  const [mode, setMode] = useState<"api" | "browser">(
    caseItem?.execution_mode ?? "api",
  );
  const [input, setInput] = useState(
    JSON.stringify(caseItem?.input ?? {}, null, 2),
  );
  const [expected, setExpected] = useState(
    JSON.stringify(caseItem?.expected_outcome ?? {}, null, 2),
  );
  const [assertions, setAssertions] = useState(
    JSON.stringify(caseItem?.assertions ?? [], null, 2),
  );
  const [error, setError] = useState("");

  async function submit() {
    try {
      const parsedInput = JSON.parse(input) as Record<string, unknown>;
      const parsedExpected = JSON.parse(expected) as Record<string, unknown>;
      const parsedAssertions = JSON.parse(assertions) as Array<
        Record<string, unknown>
      >;
      if (!name.trim()) {
        setError("请输入用例名称");
        return;
      }
      await onSubmit({
        assertions: parsedAssertions,
        execution_mode: mode,
        expected_outcome: parsedExpected,
        input: parsedInput,
        name: name.trim(),
      });
      setOpen(false);
      setError("");
    } catch {
      setError("JSON 格式无效或保存失败，请检查后重试。");
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant={caseItem ? "secondary" : "primary"}>
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogTitle>{caseItem ? "编辑测试用例" : "添加测试用例"}</DialogTitle>
        <DialogDescription>
          使用结构化 JSON 定义输入、期望结果和断言。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            用例名称
            <Input
              className="mt-1.5"
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="block text-sm font-medium">
            执行模式
            <select
              className="mt-1.5 h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3"
              onChange={(event) =>
                setMode(event.target.value as "api" | "browser")
              }
              value={mode}
            >
              <option value="api">API</option>
              <option value="browser">浏览器</option>
            </select>
          </label>
          <JsonField label="输入 JSON" onChange={setInput} value={input} />
          <JsonField
            label="期望结果 JSON"
            onChange={setExpected}
            value={expected}
          />
          <JsonField
            label="断言 JSON"
            onChange={setAssertions}
            value={assertions}
          />
          {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
          <div className="flex justify-end gap-2">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button onClick={submit} variant="primary">
              保存用例
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function JsonField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <textarea
        aria-label={label}
        className="mt-1.5 min-h-24 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 font-mono text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      />
    </label>
  );
}
