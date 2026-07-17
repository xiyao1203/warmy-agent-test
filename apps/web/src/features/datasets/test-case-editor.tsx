"use client";

import type {
  AutomationStatus,
  CreateTestCaseRequest,
  ExecutionMode,
  Priority,
  RiskLevel,
  TestCaseResponse,
  TestCaseTemplate,
  TestCaseType,
  TestGroup,
} from "@warmy/generated-api-client";
import type { ReactNode } from "react";
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
import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";

import { TestCaseDataBindings } from "./test-case-data-bindings";
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
  newFormRowId,
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
import {
  compactArtifacts,
  compactDataBindings,
  compactSteps,
  compactStringRows,
  dataBindingRows,
  parseJsonObject,
  stepRows,
  stringRows,
  type ArtifactRequirementRow,
  type DataBindingRow,
  type StringRow,
  type TestStepRow,
} from "./test-case-professional-fields";
import { TestCaseStepEditor } from "./test-case-step-editor";
import { StringListEditor } from "./test-case-string-list-editor";
import { TestCaseValidation } from "./test-case-validation";

type Section =
  | "basic"
  | "preparation"
  | "input"
  | "steps"
  | "verification"
  | "closing"
  | "advanced";

type TestCaseEditorProps = {
  caseItem?: TestCaseResponse;
  onSubmit: (payload: CreateTestCaseRequest) => Promise<unknown>;
  triggerAriaLabel?: string;
  triggerIcon?: ReactNode;
  triggerLabel: string;
};

const sections: Array<{ key: Section; label: string }> = [
  { key: "basic", label: "基本信息" },
  { key: "preparation", label: "测试准备" },
  { key: "input", label: "输入数据" },
  { key: "steps", label: "操作步骤" },
  { key: "verification", label: "断言、评分与安全" },
  { key: "closing", label: "收尾与执行" },
  { key: "advanced", label: "高级 JSON" },
];

export function TestCaseEditor({
  caseItem,
  onSubmit,
  triggerAriaLabel,
  triggerIcon,
  triggerLabel,
}: TestCaseEditorProps) {
  const [open, setOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<Section>("basic");
  const [name, setName] = useState(caseItem?.name ?? "");
  const [objective, setObjective] = useState(caseItem?.objective ?? "");
  const [template, setTemplate] = useState<TestCaseTemplate>(
    caseItem?.template ?? "step_by_step",
  );
  const [caseType, setCaseType] = useState<TestCaseType>(
    caseItem?.case_type ?? "functional",
  );
  const [automationStatus, setAutomationStatus] = useState<AutomationStatus>(
    caseItem?.automation_status ?? "manual",
  );
  const [component, setComponent] = useState(caseItem?.component ?? "");
  const [requirements, setRequirements] = useState(
    caseItem?.requirement_refs.join(", ") ?? "",
  );
  const [ownerId, setOwnerId] = useState(caseItem?.owner_id ?? "");
  const [scenario, setScenario] = useState(caseItem?.scenario ?? "");
  const [priority, setPriority] = useState<Priority | "">(
    caseItem?.priority ?? "",
  );
  const [riskLevel, setRiskLevel] = useState<RiskLevel | "">(
    caseItem?.risk_level ?? "",
  );
  const [difficulty, setDifficulty] = useState(caseItem?.difficulty ?? "");
  const [testGroup, setTestGroup] = useState<TestGroup | "">(
    caseItem?.test_group ?? "",
  );
  const [tags, setTags] = useState(caseItem?.tags.join(", ") ?? "");
  const [preconditions, setPreconditions] = useState<StringRow[]>(
    stringRows(caseItem?.preconditions),
  );
  const [postconditions, setPostconditions] = useState<StringRow[]>(
    stringRows(caseItem?.postconditions),
  );
  const [inputRows, setInputRows] = useState<KeyValueRow[]>(
    recordToRows(caseItem?.input ?? {}),
  );
  const [initialStateRows, setInitialStateRows] = useState<KeyValueRow[]>(
    recordToRows(caseItem?.initial_state ?? {}),
  );
  const [dataBindings, setDataBindings] = useState<DataBindingRow[]>(
    dataBindingRows(caseItem?.data_bindings),
  );
  const [steps, setSteps] = useState<TestStepRow[]>(stepRows(caseItem?.steps));
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
  const [artifacts, setArtifacts] = useState<ArtifactRequirementRow[]>(
    (caseItem?.artifact_requirements ?? []).flatMap((item) =>
      item && typeof item === "object"
        ? [
            {
              id: newFormRowId(),
              kind: (item.kind as ArtifactRequirementRow["kind"]) ?? "response",
              label: typeof item.label === "string" ? item.label : "",
              required: item.required !== false,
            },
          ]
        : [],
    ),
  );
  const [mode, setMode] = useState<ExecutionMode>(
    caseItem?.execution_mode ?? "api",
  );
  const [estimatedDuration, setEstimatedDuration] = useState(
    caseItem?.estimated_duration_seconds?.toString() ?? "",
  );
  const [timeout, setTimeoutSeconds] = useState(
    caseItem?.timeout_seconds?.toString() ?? "",
  );
  const [retryCount, setRetryCount] = useState(
    caseItem?.retry_count?.toString() ?? "0",
  );
  const [customFields, setCustomFields] = useState(
    JSON.stringify(caseItem?.custom_fields ?? {}, null, 2),
  );
  const [error, setError] = useState("");

  async function submit() {
    try {
      if (!name.trim()) throw new Error("请输入用例名称");
      const parsedSteps = compactSteps(steps);
      if (template === "step_by_step" && parsedSteps.length > 0) {
        const invalidStep = parsedSteps.find(
          (step) => !step.action || !step.expected_result,
        );
        if (invalidStep)
          throw new Error("每个操作步骤都必须填写操作和预期结果");
      }
      const payload: CreateTestCaseRequest = {
        artifact_requirements: compactArtifacts(artifacts),
        assertions: rowsToAssertions(assertionRows),
        automation_status: automationStatus,
        case_type: caseType,
        component: component.trim() || undefined,
        custom_fields: parseJsonObject(customFields, "高级自定义字段"),
        data_bindings: compactDataBindings(dataBindings),
        difficulty: difficulty || undefined,
        estimated_duration_seconds: optionalPositiveInteger(estimatedDuration),
        execution_mode: mode,
        expected_outcome: rowsToRecord(expectedRows),
        initial_state: rowsToRecord(initialStateRows),
        input: rowsToRecord(inputRows),
        name: name.trim(),
        objective: objective.trim() || name.trim(),
        owner_id: ownerId.trim() || undefined,
        postconditions: compactStringRows(postconditions),
        preconditions: compactStringRows(preconditions),
        priority: priority || undefined,
        requirement_refs: commaValues(requirements),
        retry_count: optionalInteger(retryCount) ?? 0,
        risk_level: riskLevel || undefined,
        scenario: scenario.trim() || undefined,
        scorers: rowsToScorers(scorerRows),
        security_policies: rowsToSecurityPolicies(securityPolicyRows),
        source_ref: caseItem?.source_ref ?? undefined,
        steps: parsedSteps,
        tags: commaValues(tags),
        template,
        test_group: testGroup || undefined,
        timeout_seconds: optionalPositiveInteger(timeout),
      };
      await onSubmit(payload);
      setOpen(false);
      setError("");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "保存失败，请检查必填项后重试。",
      );
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
      <DialogContent className="max-h-[94vh] max-w-5xl overflow-y-auto">
        <DialogTitle>
          {caseItem ? "编辑专业测试用例" : "新增专业测试用例"}
        </DialogTitle>
        <DialogDescription>
          按测试工程师标准维护准备、输入、操作步骤、逐步预期、断言、安全与执行设置。
        </DialogDescription>

        <div className="mt-2 flex flex-wrap items-center gap-2">
          {caseItem?.case_key && (
            <Badge tone="neutral">{caseItem.case_key}</Badge>
          )}
          <Badge
            tone={caseItem?.case_status === "ready" ? "accent" : "neutral"}
          >
            {caseItem?.case_status === "ready" ? "已就绪" : "草稿"}
          </Badge>
          {caseItem && <Badge>{sourceLabel(caseItem.source)}</Badge>}
          {caseItem?.source_ref && (
            <span className="text-xs text-[var(--muted)]">
              来源：{caseItem.source_ref}
            </span>
          )}
        </div>

        <div className="mt-4 flex flex-wrap gap-1 border-b border-[var(--hairline)] pb-2">
          {sections.map((section) => (
            <button
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                activeSection === section.key
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--muted)] hover:bg-[var(--canvas-soft)]"
              }`}
              key={section.key}
              onClick={() => setActiveSection(section.key)}
              type="button"
            >
              {section.label}
            </button>
          ))}
        </div>

        <div className="mt-4 space-y-5">
          {activeSection === "basic" && (
            <BasicFields
              automationStatus={automationStatus}
              caseType={caseType}
              component={component}
              difficulty={difficulty}
              name={name}
              objective={objective}
              onAutomationStatus={setAutomationStatus}
              onCaseType={setCaseType}
              onComponent={setComponent}
              onDifficulty={setDifficulty}
              onName={setName}
              onObjective={setObjective}
              onOwnerId={setOwnerId}
              onPriority={setPriority}
              onRequirements={setRequirements}
              onRiskLevel={setRiskLevel}
              onScenario={setScenario}
              onTags={setTags}
              onTemplate={setTemplate}
              onTestGroup={setTestGroup}
              ownerId={ownerId}
              priority={priority}
              requirements={requirements}
              riskLevel={riskLevel}
              scenario={scenario}
              tags={tags}
              template={template}
              testGroup={testGroup}
            />
          )}

          {activeSection === "preparation" && (
            <>
              <StringListEditor
                addLabel="添加前置条件"
                label="前置条件"
                onChange={setPreconditions}
                rows={preconditions}
              />
              <KeyValueEditor
                addLabel="添加状态字段"
                keyPlaceholder="字段名，如 user_tier"
                label="初始业务状态"
                onChange={setInitialStateRows}
                rows={initialStateRows}
                valuePlaceholder="字段值，如 free"
              />
              <TestCaseDataBindings
                onChange={setDataBindings}
                rows={dataBindings}
              />
            </>
          )}

          {activeSection === "input" && (
            <KeyValueEditor
              addLabel="添加输入字段"
              keyPlaceholder="字段名，如 message"
              label="输入数据"
              onChange={setInputRows}
              required
              rows={inputRows}
              valuePlaceholder="字段值支持文本、数字、布尔和 JSON"
            />
          )}

          {activeSection === "steps" && (
            <TestCaseStepEditor onChange={setSteps} rows={steps} />
          )}

          {activeSection === "verification" && (
            <>
              <KeyValueEditor
                addLabel="添加整体预期"
                keyPlaceholder="字段名，如 refused"
                label="整体预期结果"
                onChange={setExpectedRows}
                rows={expectedRows}
                valuePlaceholder="期望值"
              />
              <AssertionEditor
                onChange={setAssertionRows}
                rows={assertionRows}
              />
              <ScorerEditor onChange={setScorerRows} rows={scorerRows} />
              <SecurityPolicyEditor
                onChange={setSecurityPolicyRows}
                rows={securityPolicyRows}
              />
              <EvidenceEditor onChange={setArtifacts} rows={artifacts} />
            </>
          )}

          {activeSection === "closing" && (
            <>
              <StringListEditor
                addLabel="添加后置条件"
                label="后置条件"
                onChange={setPostconditions}
                rows={postconditions}
              />
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Field label="执行模式">
                  <DropdownSelect
                    aria-label="执行模式"
                    onChange={(event) =>
                      setMode(event.target.value as ExecutionMode)
                    }
                    value={mode}
                  >
                    <option value="api">API</option>
                    <option value="browser">浏览器</option>
                    <option value="codex_explore">Codex 浏览器探索</option>
                  </DropdownSelect>
                </Field>
                <Field label="预计时长（秒）">
                  <Input
                    aria-label="预计时长（秒）"
                    inputMode="numeric"
                    onChange={(event) =>
                      setEstimatedDuration(event.target.value)
                    }
                    value={estimatedDuration}
                  />
                </Field>
                <Field label="超时时间（秒）">
                  <Input
                    aria-label="超时时间（秒）"
                    inputMode="numeric"
                    onChange={(event) => setTimeoutSeconds(event.target.value)}
                    value={timeout}
                  />
                </Field>
                <Field label="重试次数">
                  <Input
                    aria-label="重试次数"
                    inputMode="numeric"
                    onChange={(event) => setRetryCount(event.target.value)}
                    value={retryCount}
                  />
                </Field>
              </div>
            </>
          )}

          {activeSection === "advanced" && (
            <label className="block text-sm font-medium">
              高级自定义字段（JSON 对象，最大 16 KiB）
              <textarea
                aria-label="高级自定义字段"
                className="mt-2 min-h-64 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] p-3 font-mono text-xs"
                onChange={(event) => setCustomFields(event.target.value)}
                spellCheck={false}
                value={customFields}
              />
            </label>
          )}

          <TestCaseValidation error={error} />

          <div className="flex flex-wrap justify-between gap-2 border-t border-[var(--hairline)] pt-4">
            <p className="text-xs text-[var(--muted)]">
              保存后可在用例行中校验、标记就绪或发起 AI 单用例试运行。
            </p>
            <div className="flex gap-2">
              <Button onClick={() => setOpen(false)}>取消</Button>
              <Button onClick={() => void submit()} variant="primary">
                保存草稿
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

type BasicFieldProps = {
  automationStatus: AutomationStatus;
  caseType: TestCaseType;
  component: string;
  difficulty: string;
  name: string;
  objective: string;
  ownerId: string;
  priority: Priority | "";
  requirements: string;
  riskLevel: RiskLevel | "";
  scenario: string;
  tags: string;
  template: TestCaseTemplate;
  testGroup: TestGroup | "";
  onAutomationStatus: (value: AutomationStatus) => void;
  onCaseType: (value: TestCaseType) => void;
  onComponent: (value: string) => void;
  onDifficulty: (value: string) => void;
  onName: (value: string) => void;
  onObjective: (value: string) => void;
  onOwnerId: (value: string) => void;
  onPriority: (value: Priority | "") => void;
  onRequirements: (value: string) => void;
  onRiskLevel: (value: RiskLevel | "") => void;
  onScenario: (value: string) => void;
  onTags: (value: string) => void;
  onTemplate: (value: TestCaseTemplate) => void;
  onTestGroup: (value: TestGroup | "") => void;
};

function BasicFields(props: BasicFieldProps) {
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="用例名称" required>
          <Input
            aria-label="用例名称"
            onChange={(event) => props.onName(event.target.value)}
            placeholder="用可验证的行为描述用例"
            value={props.name}
          />
        </Field>
        <Field label="所属组件">
          <Input
            aria-label="所属组件"
            onChange={(event) => props.onComponent(event.target.value)}
            placeholder="如 客服 / 支付 / 搜索"
            value={props.component}
          />
        </Field>
      </div>
      <Field label="测试目标" required>
        <textarea
          aria-label="测试目标"
          className="min-h-24 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] p-3 text-sm"
          onChange={(event) => props.onObjective(event.target.value)}
          placeholder="说明要验证的行为、边界和成功标准"
          value={props.objective}
        />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SelectField
          label="用例模板"
          value={props.template}
          onChange={props.onTemplate}
        >
          <option value="step_by_step">标准步骤</option>
          <option value="text">文本场景</option>
          <option value="bdd">BDD</option>
          <option value="ai_eval">AI 评测</option>
        </SelectField>
        <SelectField
          label="用例类型"
          value={props.caseType}
          onChange={props.onCaseType}
        >
          <option value="functional">功能</option>
          <option value="regression">回归</option>
          <option value="smoke">冒烟</option>
          <option value="integration">集成</option>
          <option value="e2e">端到端</option>
          <option value="security">安全</option>
          <option value="performance">性能</option>
          <option value="usability">可用性</option>
          <option value="exploratory">探索</option>
        </SelectField>
        <SelectField
          label="自动化状态"
          value={props.automationStatus}
          onChange={props.onAutomationStatus}
        >
          <option value="manual">人工</option>
          <option value="candidate">自动化候选</option>
          <option value="automated">已自动化</option>
        </SelectField>
        <SelectField
          label="优先级"
          value={props.priority}
          onChange={props.onPriority}
        >
          <option value="">未设置</option>
          <option value="P0">P0 - 最高</option>
          <option value="P1">P1 - 高</option>
          <option value="P2">P2 - 中</option>
          <option value="P3">P3 - 低</option>
        </SelectField>
        <SelectField
          label="风险等级"
          value={props.riskLevel}
          onChange={props.onRiskLevel}
        >
          <option value="">未设置</option>
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </SelectField>
        <SelectField
          label="难度"
          value={props.difficulty}
          onChange={props.onDifficulty}
        >
          <option value="">未设置</option>
          <option value="easy">简单</option>
          <option value="medium">中等</option>
          <option value="hard">困难</option>
        </SelectField>
        <SelectField
          label="测试分组"
          value={props.testGroup}
          onChange={props.onTestGroup}
        >
          <option value="">未设置</option>
          <option value="train">训练集</option>
          <option value="validation">验证集</option>
          <option value="test">测试集</option>
        </SelectField>
        <Field label="负责人 ID">
          <Input
            aria-label="负责人 ID"
            onChange={(event) => props.onOwnerId(event.target.value)}
            value={props.ownerId}
          />
        </Field>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="业务场景">
          <Input
            aria-label="业务场景"
            onChange={(event) => props.onScenario(event.target.value)}
            value={props.scenario}
          />
        </Field>
        <Field label="需求引用">
          <Input
            aria-label="需求引用"
            onChange={(event) => props.onRequirements(event.target.value)}
            placeholder="多个引用用逗号分隔"
            value={props.requirements}
          />
        </Field>
        <Field label="标签">
          <Input
            aria-label="标签"
            onChange={(event) => props.onTags(event.target.value)}
            placeholder="多个标签用逗号分隔"
            value={props.tags}
          />
        </Field>
      </div>
    </>
  );
}

function SelectField<T extends string>({
  children,
  label,
  onChange,
  value,
}: {
  children: ReactNode;
  label: string;
  onChange: (value: T) => void;
  value: T;
}) {
  return (
    <Field label={label}>
      <DropdownSelect
        aria-label={label}
        onChange={(event) => onChange(event.target.value as T)}
        value={value}
      >
        {children}
      </DropdownSelect>
    </Field>
  );
}

function EvidenceEditor({
  onChange,
  rows,
}: {
  onChange: (rows: ArtifactRequirementRow[]) => void;
  rows: ArtifactRequirementRow[];
}) {
  const kinds: ArtifactRequirementRow["kind"][] = [
    "response",
    "screenshot",
    "trace",
    "canvas_snapshot",
    "file",
  ];
  return (
    <div>
      <p className="text-sm font-medium">证据要求</p>
      <div className="mt-2 flex flex-wrap gap-3">
        {kinds.map((kind) => {
          const selected = rows.some((row) => row.kind === kind);
          return (
            <label className="flex items-center gap-2 text-xs" key={kind}>
              <input
                checked={selected}
                onChange={(event) =>
                  onChange(
                    event.target.checked
                      ? [
                          ...rows,
                          {
                            id: newFormRowId(),
                            kind,
                            label: "",
                            required: true,
                          },
                        ]
                      : rows.filter((row) => row.kind !== kind),
                  )
                }
                type="checkbox"
              />
              {artifactLabel(kind)}
            </label>
          );
        })}
      </div>
    </div>
  );
}

function artifactLabel(kind: ArtifactRequirementRow["kind"]) {
  return {
    canvas_snapshot: "画布快照",
    file: "文件",
    response: "响应",
    screenshot: "截图",
    trace: "Trace",
  }[kind];
}

function sourceLabel(source: TestCaseResponse["source"]) {
  return {
    agent_generated: "AI 生成",
    imported: "导入",
    manual: "人工创建",
    run_regression: "运行回归",
  }[source];
}

function commaValues(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function optionalInteger(value: string) {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 0)
    throw new Error("执行参数必须是非负整数");
  return parsed;
}

function optionalPositiveInteger(value: string) {
  const parsed = optionalInteger(value);
  if (parsed === undefined) return undefined;
  if (parsed < 1) throw new Error("时长和超时必须大于 0");
  return parsed;
}
