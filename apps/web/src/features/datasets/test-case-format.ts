import type { CreateTestCaseRequest } from "@warmy/generated-api-client";

export type TestCaseImportFormat = "json" | "jsonl" | "csv";

type TestCaseFieldKey = keyof CreateTestCaseRequest;

type TestCaseFieldDefinition = {
  key: TestCaseFieldKey;
  label: string;
  required: boolean;
};

export const TEST_CASE_REQUIRED_FIELDS = [
  "name",
  "input",
  "execution_mode",
] as const satisfies readonly TestCaseFieldKey[];

export const TEST_CASE_OPTIONAL_FIELDS = [
  "initial_state",
  "expected_outcome",
  "assertions",
  "scorers",
  "security_policies",
  "tags",
  "scenario",
  "priority",
  "risk_level",
  "difficulty",
  "test_group",
] as const satisfies readonly TestCaseFieldKey[];

export const TEST_CASE_FIELD_DEFINITIONS = [
  { key: "name", label: "用例名称", required: true },
  { key: "input", label: "输入", required: true },
  { key: "execution_mode", label: "执行模式", required: true },
  { key: "initial_state", label: "初始状态", required: false },
  { key: "expected_outcome", label: "期望结果", required: false },
  { key: "assertions", label: "断言规则", required: false },
  { key: "scorers", label: "评分器", required: false },
  { key: "security_policies", label: "安全策略", required: false },
  { key: "tags", label: "标签", required: false },
  { key: "scenario", label: "业务场景", required: false },
  { key: "priority", label: "优先级", required: false },
  { key: "risk_level", label: "风险等级", required: false },
  { key: "difficulty", label: "难度", required: false },
  { key: "test_group", label: "测试分组", required: false },
] as const satisfies readonly TestCaseFieldDefinition[];

export const TEST_CASE_REQUIRED_FIELD_LABELS =
  TEST_CASE_FIELD_DEFINITIONS.filter((field) => field.required).map(
    (field) => field.label,
  );

export const TEST_CASE_OPTIONAL_FIELD_LABELS =
  TEST_CASE_FIELD_DEFINITIONS.filter((field) => !field.required).map(
    (field) => field.label,
  );

export const TEST_CASE_FIELD_HELP = [
  "模板默认使用中文字段名，也兼容 name、input、execution_mode 等英文旧字段。",
  "必填：用例名称、输入、执行模式。",
  "执行模式：API、浏览器或 Codex 浏览器探索，也兼容 api/browser/codex_explore。",
  "优先级：P0、P1、P2、P3；风险等级：严重、高、中、低。",
  "测试分组：训练集、验证集、测试集。",
  "输入、初始状态、期望结果填写 JSON 对象；断言规则、评分器、安全策略填写对象数组；标签填写字符串数组。",
];

export const STANDARD_TEST_CASE_TEMPLATE: CreateTestCaseRequest = {
  name: "问候 API 正常响应",
  input: {
    message: "你好",
    locale: "zh-CN",
  },
  execution_mode: "api",
  initial_state: {
    user_tier: "free",
  },
  expected_outcome: {
    contains: "你好",
  },
  assertions: [
    {
      type: "contains",
      path: "output.text",
      value: "你好",
    },
  ],
  scorers: [
    {
      type: "llm_judge",
      name: "helpfulness",
      threshold: 0.8,
    },
  ],
  security_policies: [
    {
      type: "pii_redaction",
      severity: "medium",
    },
  ],
  tags: ["smoke", "api"],
  scenario: "基础问候",
  priority: "P1",
  risk_level: "low",
  difficulty: "easy",
  test_group: "test",
};

const LOCALIZED_TEMPLATE_VALUES: Partial<Record<TestCaseFieldKey, unknown>> = {
  execution_mode: "API",
  risk_level: "低",
  difficulty: "简单",
  test_group: "测试集",
};

export function buildTestCaseTemplate(format: TestCaseImportFormat) {
  const localizedTemplate = localizeTemplate(STANDARD_TEST_CASE_TEMPLATE);
  if (format === "json") {
    return JSON.stringify([localizedTemplate], null, 2);
  }
  if (format === "jsonl") {
    return `${JSON.stringify(localizedTemplate)}\n`;
  }
  return buildCsvTemplate(localizedTemplate);
}

export function testCaseTemplateFilename(format: TestCaseImportFormat) {
  return `test-cases-cn-template.${format}`;
}

function localizeTemplate(template: CreateTestCaseRequest) {
  return Object.fromEntries(
    TEST_CASE_FIELD_DEFINITIONS.map((field) => [
      field.label,
      LOCALIZED_TEMPLATE_VALUES[field.key] ?? template[field.key],
    ]),
  );
}

function buildCsvTemplate(template: Record<string, unknown>) {
  const headers = TEST_CASE_FIELD_DEFINITIONS.map((field) => field.label);
  const row = headers.map((field) => escapeCsvValue(template[field])).join(",");
  return `${headers.join(",")}\n${row}\n`;
}

function escapeCsvValue(value: unknown) {
  const text =
    typeof value === "string" ? value : JSON.stringify(value ?? "", null, 0);
  return `"${text.replaceAll('"', '""')}"`;
}
