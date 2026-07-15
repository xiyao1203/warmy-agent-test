"use client";

import type {
  CreateTestCaseRequest,
  ExecutionMode,
  Priority,
  RiskLevel,
  TestCaseResponse,
  TestGroup,
} from "@warmy/generated-api-client";
import type { ReactNode } from "react";
import { useState } from "react";

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
import {
  AssertionEditor,
  Field,
  KeyValueEditor,
  ScorerEditor,
  SecurityPolicyEditor,
} from "./test-case-editors";
import {
  assertionsToRows,
  type AssertionRow,
  type KeyValueRow,
  recordToRows,
  rowsToAssertions,
  rowsToRecord,
  rowsToScorers,
  rowsToSecurityPolicies,
  scorersToRows,
  type ScorerRow,
  securityPoliciesToRows,
  type SecurityPolicyRow,
} from "./test-case-form-codecs";

type TestCaseEditorProps = {
  caseItem?: TestCaseResponse;
  onSubmit: (payload: CreateTestCaseRequest) => Promise<unknown>;
  triggerAriaLabel?: string;
  triggerIcon?: ReactNode;
  triggerLabel: string;
};

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
  const [mode, setMode] = useState<ExecutionMode>(
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
                  aria-label="执行模式"
                  className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
                  onChange={(e) => setMode(e.target.value as ExecutionMode)}
                  value={mode}
                >
                  <option value="api">API</option>
                  <option value="browser">浏览器</option>
                  <option value="codex_explore">Codex 浏览器探索</option>
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
                  <Badge>{executionModeLabel(mode)}模式</Badge>
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

function executionModeLabel(mode: ExecutionMode) {
  if (mode === "api") return "API ";
  if (mode === "codex_explore") return "Codex 浏览器探索";
  return "浏览器";
}
