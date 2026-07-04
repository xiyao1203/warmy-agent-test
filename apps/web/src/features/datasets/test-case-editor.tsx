"use client";

import type {
  CreateTestCaseRequest,
  Priority,
  RiskLevel,
  TestCaseResponse,
  TestGroup,
} from "@warmy/generated-api-client";
import type { ReactNode } from "react";
import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

type TestCaseEditorProps = {
  caseItem?: TestCaseResponse;
  onSubmit: (payload: CreateTestCaseRequest) => Promise<unknown>;
  triggerAriaLabel?: string;
  triggerIcon?: ReactNode;
  triggerLabel: string;
};

type KeyValueRow = { id: string; key: string; value: string };
type AssertionRow = { id: string; type: string; path: string; value: string };
type ScorerRow = { id: string; name: string; type: string; threshold: string };
type SecurityPolicyRow = { id: string; type: string; severity: string };

export function TestCaseEditor({
  caseItem,
  onSubmit,
  triggerAriaLabel,
  triggerIcon,
  triggerLabel,
}: TestCaseEditorProps) {
  const [open, setOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<
    "basic" | "input" | "output" | "scoring" | "advanced"
  >("basic");

  // 基本信息
  const [name, setName] = useState(caseItem?.name ?? "");
  const [mode, setMode] = useState<"api" | "browser">(
    caseItem?.execution_mode ?? "api",
  );
  const [scenario, setScenario] = useState(caseItem?.scenario ?? "");
  const [priority, setPriority] = useState<Priority | "">(
    caseItem?.priority ?? "",
  );
  const [riskLevel, setRiskLevel] = useState<RiskLevel | "">(
    caseItem?.risk_level ?? "",
  );
  const [difficulty, setDifficulty] = useState<string>(
    caseItem?.difficulty ?? "",
  );
  const [testGroup, setTestGroup] = useState<TestGroup | "">(
    caseItem?.test_group ?? "",
  );
  const [tags, setTags] = useState<string>(
    Array.isArray(caseItem?.tags) ? caseItem.tags.join(", ") : "",
  );

  const [inputRows, setInputRows] = useState<KeyValueRow[]>(
    recordToRows(caseItem?.input ?? {}),
  );
  const [initialStateRows, setInitialStateRows] = useState<KeyValueRow[]>(
    recordToRows(caseItem?.initial_state ?? {}),
  );
  const [expectedRows, setExpectedRows] = useState<KeyValueRow[]>(
    recordToRows(caseItem?.expected_outcome ?? {}),
  );
  const [assertionRows, setAssertionRows] = useState<AssertionRow[]>(
    assertionsToRows(caseItem?.assertions ?? []),
  );
  const [scorerRows, setScorerRows] = useState<ScorerRow[]>(
    scorersToRows(caseItem?.scorers ?? []),
  );
  const [securityPolicyRows, setSecurityPolicyRows] = useState<
    SecurityPolicyRow[]
  >(securityPoliciesToRows(caseItem?.security_policies ?? []));

  const [error, setError] = useState("");

  const sections = [
    { key: "basic", label: "基本信息" },
    { key: "input", label: "输入数据" },
    { key: "output", label: "预期与断言" },
    { key: "scoring", label: "评分与安全" },
    { key: "advanced", label: "高级选项" },
  ] as const;

  async function submit() {
    try {
      const parsedInput = rowsToRecord(inputRows);
      const parsedExpected = rowsToRecord(expectedRows);
      const parsedAssertions = rowsToAssertions(assertionRows);
      const parsedScorers = rowsToScorers(scorerRows);
      const parsedSecurityPolicies = rowsToSecurityPolicies(securityPolicyRows);
      const parsedInitialState = rowsToRecord(initialStateRows);

      if (!name.trim()) {
        setError("请输入用例名称");
        return;
      }

      const payload: CreateTestCaseRequest = {
        assertions: parsedAssertions,
        execution_mode: mode,
        expected_outcome: parsedExpected,
        input: parsedInput,
        name: name.trim(),
        initial_state: parsedInitialState,
        scorers: parsedScorers,
        security_policies: parsedSecurityPolicies,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        scenario: scenario || undefined,
        priority: priority || undefined,
        risk_level: riskLevel || undefined,
        difficulty: difficulty || undefined,
        test_group: testGroup || undefined,
      };

      await onSubmit(payload);
      setOpen(false);
      setError("");
    } catch {
      setError("保存失败，请检查必填项后重试。");
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button
          aria-label={triggerAriaLabel}
          className="shrink-0 whitespace-nowrap"
          variant={caseItem ? "secondary" : "primary"}
        >
          {triggerIcon}
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogTitle>{caseItem ? "编辑测试用例" : "新增测试用例"}</DialogTitle>
        <DialogDescription>
          定义测试用例的输入、预期输出、断言和评分规则。
        </DialogDescription>

        {/* 分区导航 */}
        <div className="flex gap-1 border-b border-[var(--hairline)] pb-2">
          {sections.map((section) => (
            <button
              key={section.key}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                activeSection === section.key
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--muted)] hover:bg-[var(--canvas-soft)]"
              }`}
              onClick={() => setActiveSection(section.key)}
            >
              {section.label}
            </button>
          ))}
        </div>

        <div className="mt-4 space-y-4">
          {/* 基本信息 */}
          {activeSection === "basic" && (
            <>
              <Field label="用例名称" required>
                <Input
                  aria-label="用例名称"
                  onChange={(e) => setName(e.target.value)}
                  placeholder="输入用例名称"
                  value={name}
                />
              </Field>
              <Field label="执行模式">
                <DropdownSelect
                  className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
                  onChange={(e) => setMode(e.target.value as "api" | "browser")}
                  value={mode}
                >
                  <option value="api">API</option>
                  <option value="browser">浏览器</option>
                </DropdownSelect>
              </Field>
              <Field label="业务场景">
                <Input
                  onChange={(e) => setScenario(e.target.value)}
                  placeholder="如：登录、支付、搜索"
                  value={scenario}
                />
              </Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label="优先级">
                  <DropdownSelect
                    aria-label="优先级"
                    className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
                    onChange={(e) =>
                      setPriority(e.target.value as Priority | "")
                    }
                    value={priority}
                  >
                    <option value="">未设置</option>
                    <option value="P0">P0 - 最高</option>
                    <option value="P1">P1 - 高</option>
                    <option value="P2">P2 - 中</option>
                    <option value="P3">P3 - 低</option>
                  </DropdownSelect>
                </Field>
                <Field label="风险等级">
                  <DropdownSelect
                    aria-label="风险等级"
                    className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
                    onChange={(e) =>
                      setRiskLevel(e.target.value as RiskLevel | "")
                    }
                    value={riskLevel}
                  >
                    <option value="">未设置</option>
                    <option value="high">高风险</option>
                    <option value="medium">中风险</option>
                    <option value="low">低风险</option>
                  </DropdownSelect>
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Field label="难度">
                  <DropdownSelect
                    aria-label="难度"
                    className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
                    onChange={(e) => setDifficulty(e.target.value)}
                    value={difficulty}
                  >
                    <option value="">未设置</option>
                    <option value="easy">简单</option>
                    <option value="medium">中等</option>
                    <option value="hard">困难</option>
                  </DropdownSelect>
                </Field>
                <Field label="测试分组">
                  <DropdownSelect
                    aria-label="测试分组"
                    className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
                    onChange={(e) =>
                      setTestGroup(e.target.value as TestGroup | "")
                    }
                    value={testGroup}
                  >
                    <option value="">未设置</option>
                    <option value="train">训练集</option>
                    <option value="validation">验证集</option>
                    <option value="test">测试集</option>
                  </DropdownSelect>
                </Field>
              </div>
              <Field label="标签">
                <Input
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="多个标签用逗号分隔"
                  value={tags}
                />
              </Field>
            </>
          )}

          {/* 输入数据 */}
          {activeSection === "input" && (
            <>
              <KeyValueEditor
                addLabel="添加输入字段"
                keyPlaceholder="字段名，如 message"
                label="输入数据"
                onChange={setInputRows}
                rows={inputRows}
                required
                valuePlaceholder="字段值，如 你好"
              />
              <KeyValueEditor
                addLabel="添加状态字段"
                keyPlaceholder="字段名，如 user_tier"
                label="初始业务状态"
                onChange={setInitialStateRows}
                rows={initialStateRows}
                valuePlaceholder="字段值，如 free"
              />
            </>
          )}

          {/* 预期与断言 */}
          {activeSection === "output" && (
            <>
              <KeyValueEditor
                addLabel="添加期望字段"
                keyPlaceholder="字段名，如 contains"
                label="期望结果"
                onChange={setExpectedRows}
                rows={expectedRows}
                valuePlaceholder="字段值，如 你好"
              />
              <AssertionEditor
                onChange={setAssertionRows}
                rows={assertionRows}
              />
            </>
          )}

          {/* 评分与安全 */}
          {activeSection === "scoring" && (
            <>
              <ScorerEditor onChange={setScorerRows} rows={scorerRows} />
              <SecurityPolicyEditor
                onChange={setSecurityPolicyRows}
                rows={securityPolicyRows}
              />
            </>
          )}

          {/* 高级选项 */}
          {activeSection === "advanced" && (
            <div className="space-y-4">
              <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-4">
                <h4 className="text-sm font-medium">当前配置摘要</h4>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Badge>{mode === "api" ? "API 模式" : "浏览器模式"}</Badge>
                  <Badge>
                    {assertionRows.length > 0
                      ? `${assertionRows.length} 条断言`
                      : "未配置断言"}
                  </Badge>
                  {priority && <Badge>{priority}</Badge>}
                  {riskLevel && <Badge>{riskLevel}</Badge>}
                  {difficulty && <Badge>{difficulty}</Badge>}
                  {testGroup && <Badge>{testGroup}</Badge>}
                </div>
                {tags && (
                  <div className="mt-2 text-xs text-[var(--muted)]">
                    标签：{tags}
                  </div>
                )}
              </div>
            </div>
          )}

          {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

          <div className="flex justify-end gap-2 border-t border-[var(--hairline)] pt-4">
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

/* ── 子组件 ────────────────────────────────────────────────────────── */

function newId() {
  return Math.random().toString(36).slice(2);
}

function formatCellValue(value: unknown) {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

function parseCellValue(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (trimmed === "true") return true;
  if (trimmed === "false") return false;
  if (trimmed === "null") return null;
  if (!Number.isNaN(Number(trimmed)) && /^-?\d+(\.\d+)?$/.test(trimmed)) {
    return Number(trimmed);
  }
  if (
    trimmed.startsWith("{") ||
    trimmed.startsWith("[") ||
    trimmed.startsWith('"')
  ) {
    try {
      return JSON.parse(trimmed) as unknown;
    } catch {
      return value;
    }
  }
  return value;
}

function recordToRows(record: Record<string, unknown>) {
  return Object.entries(record).map(([key, value]) => ({
    id: newId(),
    key,
    value: formatCellValue(value),
  }));
}

function rowsToRecord(rows: KeyValueRow[]) {
  return Object.fromEntries(
    rows
      .filter((row) => row.key.trim())
      .map((row) => [row.key.trim(), parseCellValue(row.value)]),
  );
}

function assertionsToRows(assertions: Array<Record<string, unknown>>) {
  return assertions.map((assertion) => ({
    id: newId(),
    type: formatCellValue(assertion.type ?? "contains"),
    path: formatCellValue(assertion.path ?? ""),
    value: formatCellValue(assertion.value ?? ""),
  }));
}

function rowsToAssertions(rows: AssertionRow[]) {
  return rows
    .filter((row) => row.path.trim() || row.value.trim())
    .map((row) => ({
      type: row.type.trim() || "contains",
      path: row.path.trim(),
      value: parseCellValue(row.value),
    }));
}

function scorersToRows(scorers: Array<Record<string, unknown>>) {
  return scorers.map((scorer) => ({
    id: newId(),
    name: formatCellValue(scorer.name ?? ""),
    type: formatCellValue(scorer.type ?? "llm_judge"),
    threshold: formatCellValue(scorer.threshold ?? ""),
  }));
}

function rowsToScorers(rows: ScorerRow[]) {
  return rows
    .filter((row) => row.name.trim())
    .map((row) => ({
      name: row.name.trim(),
      type: row.type.trim() || "llm_judge",
      threshold: row.threshold.trim() ? Number(row.threshold) : undefined,
    }));
}

function securityPoliciesToRows(policies: Array<Record<string, unknown>>) {
  return policies.map((policy) => ({
    id: newId(),
    type: formatCellValue(policy.type ?? ""),
    severity: formatCellValue(policy.severity ?? "medium"),
  }));
}

function rowsToSecurityPolicies(rows: SecurityPolicyRow[]) {
  return rows
    .filter((row) => row.type.trim())
    .map((row) => ({
      type: row.type.trim(),
      severity: row.severity.trim() || "medium",
    }));
}

function Field({
  label,
  required = false,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      {required && <span className="ml-1 text-[var(--danger)]">*</span>}
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

function KeyValueEditor({
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
        onClick={() => onChange([...rows, { id: newId(), key: "", value: "" }])}
        variant="secondary"
      >
        <Plus aria-hidden="true" className="mr-1 size-4" />
        {addLabel}
      </Button>
    </div>
  );
}

function AssertionEditor({
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
            { id: newId(), path: "", type: "contains", value: "" },
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

function ScorerEditor({
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
            { id: newId(), name: "", threshold: "0.8", type: "llm_judge" },
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

function SecurityPolicyEditor({
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
          onChange([...rows, { id: newId(), severity: "medium", type: "" }])
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
