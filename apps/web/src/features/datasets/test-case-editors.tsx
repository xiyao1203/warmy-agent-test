import type { ReactNode } from "react";
import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";
import {
  type AssertionRow,
  type KeyValueRow,
  newFormRowId,
  type ScorerRow,
  type SecurityPolicyRow,
} from "./test-case-form-codecs";

export function Field({
  label,
  required = false,
  children,
}: {
  label: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      {required && <span className="ml-1 text-[var(--danger)]">*</span>}
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

export function KeyValueEditor({
  addLabel,
  keyPlaceholder,
  label,
  onChange,
  rows,
  required = false,
  valuePlaceholder,
}: {
  addLabel: string;
  keyPlaceholder: string;
  label: string;
  onChange: (rows: KeyValueRow[]) => void;
  rows: KeyValueRow[];
  required?: boolean;
  valuePlaceholder: string;
}) {
  const updateRow = (id: string, patch: Partial<KeyValueRow>) => {
    onChange(rows.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  };

  return (
    <div>
      <div className="text-sm font-medium">
        {label}
        {required && <span className="ml-1 text-[var(--danger)]">*</span>}
      </div>
      <div className="mt-2 space-y-2">
        {rows.map((row) => (
          <div
            className="grid grid-cols-[minmax(120px,1fr)_minmax(180px,2fr)_36px] gap-2"
            key={row.id}
          >
            <Input
              aria-label={`${label}字段名`}
              onChange={(event) =>
                updateRow(row.id, { key: event.target.value })
              }
              placeholder={keyPlaceholder}
              value={row.key}
            />
            <Input
              aria-label={`${label}字段值`}
              onChange={(event) =>
                updateRow(row.id, { value: event.target.value })
              }
              placeholder={valuePlaceholder}
              value={row.value}
            />
            <IconButton
              label={`删除${label}字段`}
              onClick={() =>
                onChange(rows.filter((item) => item.id !== row.id))
              }
            />
          </div>
        ))}
      </div>
      <Button
        className="mt-2"
        onClick={() =>
          onChange([...rows, { id: newFormRowId(), key: "", value: "" }])
        }
        variant="secondary"
      >
        <Plus aria-hidden="true" className="mr-1 size-4" />
        {addLabel}
      </Button>
    </div>
  );
}

export function AssertionEditor({
  onChange,
  rows,
}: {
  onChange: (rows: AssertionRow[]) => void;
  rows: AssertionRow[];
}) {
  const updateRow = (id: string, patch: Partial<AssertionRow>) => {
    onChange(rows.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  };

  return (
    <div>
      <div className="text-sm font-medium">断言规则</div>
      <div className="mt-2 space-y-2">
        {rows.map((row) => (
          <div
            className="grid grid-cols-[120px_minmax(140px,1fr)_minmax(160px,1fr)_36px] gap-2"
            key={row.id}
          >
            <DropdownSelect
              aria-label="断言类型"
              className="h-9 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
              onChange={(event) =>
                updateRow(row.id, { type: event.target.value })
              }
              value={row.type}
            >
              <option value="contains">包含</option>
              <option value="equals">等于</option>
              <option value="exists">存在</option>
              <option value="regex">正则匹配</option>
            </DropdownSelect>
            <Input
              aria-label="断言字段"
              onChange={(event) =>
                updateRow(row.id, { path: event.target.value })
              }
              placeholder="字段，如 output.text"
              value={row.path}
            />
            <Input
              aria-label="断言期望值"
              onChange={(event) =>
                updateRow(row.id, { value: event.target.value })
              }
              placeholder="期望值"
              value={row.value}
            />
            <IconButton
              label="删除断言"
              onClick={() =>
                onChange(rows.filter((item) => item.id !== row.id))
              }
            />
          </div>
        ))}
      </div>
      <Button
        className="mt-2"
        onClick={() =>
          onChange([
            ...rows,
            {
              id: newFormRowId(),
              path: "",
              type: "contains",
              value: "",
            },
          ])
        }
        variant="secondary"
      >
        <Plus aria-hidden="true" className="mr-1 size-4" />
        添加断言
      </Button>
    </div>
  );
}

export function ScorerEditor({
  onChange,
  rows,
}: {
  onChange: (rows: ScorerRow[]) => void;
  rows: ScorerRow[];
}) {
  const updateRow = (id: string, patch: Partial<ScorerRow>) => {
    onChange(rows.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  };

  return (
    <div>
      <div className="text-sm font-medium">评分器</div>
      <div className="mt-2 space-y-2">
        {rows.map((row) => (
          <div
            className="grid grid-cols-[minmax(120px,1fr)_140px_100px_36px] gap-2"
            key={row.id}
          >
            <Input
              aria-label="评分器名称"
              onChange={(event) =>
                updateRow(row.id, { name: event.target.value })
              }
              placeholder="名称，如 helpfulness"
              value={row.name}
            />
            <DropdownSelect
              aria-label="评分器类型"
              className="h-9 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
              onChange={(event) =>
                updateRow(row.id, { type: event.target.value })
              }
              value={row.type}
            >
              <option value="llm_judge">模型裁判</option>
              <option value="rule">规则评分</option>
              <option value="visual">视觉评分</option>
            </DropdownSelect>
            <Input
              aria-label="通过阈值"
              onChange={(event) =>
                updateRow(row.id, { threshold: event.target.value })
              }
              placeholder="0.8"
              value={row.threshold}
            />
            <IconButton
              label="删除评分器"
              onClick={() =>
                onChange(rows.filter((item) => item.id !== row.id))
              }
            />
          </div>
        ))}
      </div>
      <Button
        className="mt-2"
        onClick={() =>
          onChange([
            ...rows,
            {
              id: newFormRowId(),
              name: "",
              threshold: "0.8",
              type: "llm_judge",
            },
          ])
        }
        variant="secondary"
      >
        <Plus aria-hidden="true" className="mr-1 size-4" />
        添加评分器
      </Button>
    </div>
  );
}

export function SecurityPolicyEditor({
  onChange,
  rows,
}: {
  onChange: (rows: SecurityPolicyRow[]) => void;
  rows: SecurityPolicyRow[];
}) {
  const updateRow = (id: string, patch: Partial<SecurityPolicyRow>) => {
    onChange(rows.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  };

  return (
    <div>
      <div className="text-sm font-medium">安全策略</div>
      <div className="mt-2 space-y-2">
        {rows.map((row) => (
          <div
            className="grid grid-cols-[minmax(160px,1fr)_140px_36px] gap-2"
            key={row.id}
          >
            <Input
              aria-label="安全策略类型"
              onChange={(event) =>
                updateRow(row.id, { type: event.target.value })
              }
              placeholder="策略，如 pii_redaction"
              value={row.type}
            />
            <DropdownSelect
              aria-label="安全等级"
              className="h-9 rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
              onChange={(event) =>
                updateRow(row.id, { severity: event.target.value })
              }
              value={row.severity}
            >
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
              <option value="critical">严重</option>
            </DropdownSelect>
            <IconButton
              label="删除安全策略"
              onClick={() =>
                onChange(rows.filter((item) => item.id !== row.id))
              }
            />
          </div>
        ))}
      </div>
      <Button
        className="mt-2"
        onClick={() =>
          onChange([
            ...rows,
            { id: newFormRowId(), severity: "medium", type: "" },
          ])
        }
        variant="secondary"
      >
        <Plus aria-hidden="true" className="mr-1 size-4" />
        添加安全策略
      </Button>
    </div>
  );
}

function IconButton({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      aria-label={label}
      className="grid size-9 place-items-center rounded-[var(--radius-md)] text-[var(--muted)] hover:bg-[var(--danger-subtle)] hover:text-[var(--danger)]"
      onClick={onClick}
      type="button"
    >
      <Trash2 aria-hidden="true" className="size-4" />
    </button>
  );
}
