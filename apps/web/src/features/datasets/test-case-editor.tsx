"use client";

import type {
  CreateTestCaseRequest,
  Priority,
  RiskLevel,
  TestCaseResponse,
  TestGroup,
} from "@warmy/generated-api-client";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  triggerLabel: string;
};

export function TestCaseEditor({
  caseItem,
  onSubmit,
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

  // 输入数据
  const [input, setInput] = useState(
    JSON.stringify(caseItem?.input ?? {}, null, 2),
  );
  const [initialState, setInitialState] = useState(
    JSON.stringify(caseItem?.initial_state ?? {}, null, 2),
  );

  // 预期输出
  const [expected, setExpected] = useState(
    JSON.stringify(caseItem?.expected_outcome ?? {}, null, 2),
  );
  const [assertions, setAssertions] = useState(
    JSON.stringify(caseItem?.assertions ?? [], null, 2),
  );

  // 评分与安全
  const [scorers, setScorers] = useState(
    JSON.stringify(caseItem?.scorers ?? [], null, 2),
  );
  const [securityPolicies, setSecurityPolicies] = useState(
    JSON.stringify(caseItem?.security_policies ?? [], null, 2),
  );

  const [error, setError] = useState("");

  const sections = [
    { key: "basic", label: "基本信息" },
    { key: "input", label: "输入数据" },
    { key: "output", label: "预期输出" },
    { key: "scoring", label: "评分与安全" },
    { key: "advanced", label: "高级选项" },
  ] as const;

  async function submit() {
    try {
      const parsedInput = JSON.parse(input) as Record<string, unknown>;
      const parsedExpected = JSON.parse(expected) as Record<string, unknown>;
      const parsedAssertions = JSON.parse(assertions) as Array<
        Record<string, unknown>
      >;
      const parsedScorers = JSON.parse(scorers) as Array<
        Record<string, unknown>
      >;
      const parsedSecurityPolicies = JSON.parse(securityPolicies) as Array<
        Record<string, unknown>
      >;
      const parsedInitialState = JSON.parse(initialState) as Record<
        string,
        unknown
      >;

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
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogTitle>{caseItem ? "编辑测试用例" : "添加测试用例"}</DialogTitle>
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
                <select
                  className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
                  onChange={(e) => setMode(e.target.value as "api" | "browser")}
                  value={mode}
                >
                  <option value="api">API</option>
                  <option value="browser">浏览器</option>
                </select>
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
                  <select
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
                  </select>
                </Field>
                <Field label="风险等级">
                  <select
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
                  </select>
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Field label="难度">
                  <select
                    aria-label="难度"
                    className="h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
                    onChange={(e) => setDifficulty(e.target.value)}
                    value={difficulty}
                  >
                    <option value="">未设置</option>
                    <option value="easy">简单</option>
                    <option value="medium">中等</option>
                    <option value="hard">困难</option>
                  </select>
                </Field>
                <Field label="测试分组">
                  <select
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
                  </select>
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
              <JsonField
                label="输入 JSON"
                onChange={setInput}
                value={input}
                required
              />
              <JsonField
                label="初始业务状态"
                onChange={setInitialState}
                value={initialState}
              />
            </>
          )}

          {/* 预期输出 */}
          {activeSection === "output" && (
            <>
              <JsonField
                label="期望结果 JSON"
                onChange={setExpected}
                value={expected}
              />
              <JsonField
                label="断言规则"
                onChange={setAssertions}
                value={assertions}
              />
            </>
          )}

          {/* 评分与安全 */}
          {activeSection === "scoring" && (
            <>
              <JsonField
                label="评分器配置"
                onChange={setScorers}
                value={scorers}
              />
              <JsonField
                label="安全策略"
                onChange={setSecurityPolicies}
                value={securityPolicies}
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

function JsonField({
  label,
  onChange,
  value,
  required = false,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
  required?: boolean;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      {required && <span className="ml-1 text-[var(--danger)]">*</span>}
      <textarea
        aria-label={label}
        className="mt-1.5 min-h-32 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3 py-2 font-mono text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        onChange={(e) => onChange(e.target.value)}
        value={value}
      />
    </label>
  );
}
