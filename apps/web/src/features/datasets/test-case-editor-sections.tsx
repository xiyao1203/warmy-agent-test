import type {
  AutomationStatus,
  Priority,
  RiskLevel,
  TestCaseResponse,
  TestCaseTemplate,
  TestCaseType,
  TestGroup,
} from "@warmy/generated-api-client";
import type { ReactNode } from "react";

import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";

import { Field } from "./test-case-editors";
import { newFormRowId } from "./test-case-form-codecs";
import type { ArtifactRequirementRow } from "./test-case-professional-fields";

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

export function BasicFields(props: BasicFieldProps) {
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

export function SelectField<T extends string>({
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

export function EvidenceEditor({
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

export function sourceLabel(source: TestCaseResponse["source"]) {
  return {
    agent_generated: "AI 生成",
    imported: "导入",
    manual: "人工创建",
    run_regression: "运行回归",
  }[source];
}

export function commaValues(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function optionalInteger(value: string) {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 0)
    throw new Error("执行参数必须是非负整数");
  return parsed;
}

export function optionalPositiveInteger(value: string) {
  const parsed = optionalInteger(value);
  if (parsed === undefined) return undefined;
  if (parsed < 1) throw new Error("时长和超时必须大于 0");
  return parsed;
}
