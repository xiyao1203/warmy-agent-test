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
  BasicFields,
  commaValues,
  EvidenceEditor,
  optionalInteger,
  optionalPositiveInteger,
  sourceLabel,
} from "./test-case-editor-sections";
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
                  ? "bg-[var(--primary)] text-[var(--on-primary)]"
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
                className="text-code mt-2 min-h-64 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] p-3"
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
