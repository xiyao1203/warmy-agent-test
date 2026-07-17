import type {
  ArtifactKind,
  DataBindingSource,
  DataValueType,
  TestCaseResponse,
  TestStepV1,
} from "@warmy/generated-api-client";

import {
  assertionsToRows,
  type AssertionRow,
  newFormRowId,
  rowsToAssertions,
} from "./test-case-form-codecs";

export type StringRow = { id: string; value: string };

export type DataBindingRow = {
  id: string;
  name: string;
  source: DataBindingSource;
  valueType: DataValueType;
  value: string;
  reference: string;
  sensitive: boolean;
  description: string;
};

export type ArtifactRequirementRow = {
  id: string;
  kind: ArtifactKind;
  label: string;
  required: boolean;
};

export type TestStepRow = {
  id: string;
  action: string;
  testData: string;
  expectedResult: string;
  operationAction: "" | "goto" | "click" | "fill" | "wait" | "screenshot";
  operationTarget: string;
  operationValue: string;
  assertions: AssertionRow[];
  artifacts: ArtifactRequirementRow[];
};

export function stringRows(values: string[] | undefined): StringRow[] {
  return (values ?? []).map((value) => ({ id: newFormRowId(), value }));
}

export function compactStringRows(rows: StringRow[]) {
  return rows.map((row) => row.value.trim()).filter(Boolean);
}

export function dataBindingRows(
  bindings: TestCaseResponse["data_bindings"] | undefined,
): DataBindingRow[] {
  return (bindings ?? []).map((binding) => ({
    description: text(binding.description),
    id: newFormRowId(),
    name: text(binding.name),
    reference: text(binding.reference),
    sensitive: Boolean(binding.sensitive),
    source: validBindingSource(binding.source),
    value: formatJsonValue(binding.value),
    valueType: validValueType(binding.value_type),
  }));
}

export function compactDataBindings(rows: DataBindingRow[]) {
  return rows
    .filter((row) => row.name.trim())
    .map((row) => {
      const sensitive = row.sensitive || row.source === "credential";
      return {
        description: row.description.trim() || undefined,
        name: row.name.trim(),
        reference: row.reference.trim() || undefined,
        sensitive,
        source: row.source,
        value:
          sensitive || row.source !== "literal"
            ? undefined
            : parseJsonValue(row.value, row.valueType),
        value_type: row.valueType,
      };
    });
}

export function stepRows(
  steps: TestCaseResponse["steps"] | undefined,
): TestStepRow[] {
  return (steps ?? []).map((step) => {
    const operation =
      step.operation && typeof step.operation === "object"
        ? step.operation
        : undefined;
    return {
      action: text(step.action),
      artifacts: artifactRows(step.artifact_requirements),
      assertions: assertionsToRows(asRecords(step.assertions)),
      expectedResult: text(step.expected_result),
      id: newFormRowId(),
      operationAction: validBrowserAction(operation?.action),
      operationTarget: text(operation?.target),
      operationValue: text(operation?.value),
      testData: formatJsonObject(step.test_data),
    };
  });
}

export function compactSteps(rows: TestStepRow[]): TestStepV1[] {
  return rows
    .filter((row) => row.action.trim() || row.expectedResult.trim())
    .map((row, index) => {
      const operation = row.operationAction
        ? {
            action: row.operationAction,
            ...(row.operationTarget.trim()
              ? { target: row.operationTarget.trim() }
              : {}),
            ...(row.operationValue ? { value: row.operationValue } : {}),
          }
        : undefined;
      return {
        action: row.action.trim(),
        artifact_requirements: compactArtifacts(row.artifacts),
        assertions: rowsToAssertions(row.assertions),
        expected_result: row.expectedResult.trim(),
        operation,
        step_no: index + 1,
        test_data: parseJsonObject(row.testData, `步骤 ${index + 1} 测试数据`),
      };
    });
}

export function artifactRows(value: unknown): ArtifactRequirementRow[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const record = item as Record<string, unknown>;
    return [
      {
        id: newFormRowId(),
        kind: validArtifactKind(record.kind),
        label: text(record.label),
        required: record.required !== false,
      },
    ];
  });
}

export function compactArtifacts(rows: ArtifactRequirementRow[]) {
  return rows.map((row) => ({
    kind: row.kind,
    label: row.label.trim() || undefined,
    required: row.required,
  }));
}

export function parseJsonObject(value: string, label: string) {
  const trimmed = value.trim();
  if (!trimmed) return {};
  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error(`${label}必须是合法 JSON`);
  }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(`${label}必须是 JSON 对象`);
  }
  return parsed as Record<string, unknown>;
}

function parseJsonValue(value: string, valueType: DataValueType) {
  if (valueType === "string") return value;
  if (valueType === "number") {
    const parsed = Number(value);
    if (!Number.isFinite(parsed))
      throw new Error("数值类型的数据绑定必须填写数字");
    return parsed;
  }
  if (valueType === "boolean") {
    if (value !== "true" && value !== "false") {
      throw new Error("布尔类型的数据绑定只能填写 true 或 false");
    }
    return value === "true";
  }
  if (!value.trim()) return {};
  return JSON.parse(value) as unknown;
}

function formatJsonObject(value: unknown) {
  if (!value || typeof value !== "object") return "{}";
  return JSON.stringify(value, null, 2);
}

function formatJsonValue(value: unknown) {
  if (value === undefined || value === null) return "";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function asRecords(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value)
    ? value.filter(
        (item): item is Record<string, unknown> =>
          Boolean(item) && typeof item === "object" && !Array.isArray(item),
      )
    : [];
}

function text(value: unknown) {
  return typeof value === "string" ? value : "";
}

function validBindingSource(value: unknown): DataBindingSource {
  return [
    "literal",
    "environment",
    "credential",
    "fixture",
    "generated",
  ].includes(String(value))
    ? (value as DataBindingSource)
    : "literal";
}

function validValueType(value: unknown): DataValueType {
  return ["string", "number", "boolean", "json"].includes(String(value))
    ? (value as DataValueType)
    : "string";
}

function validArtifactKind(value: unknown): ArtifactKind {
  return [
    "response",
    "screenshot",
    "trace",
    "canvas_snapshot",
    "file",
  ].includes(String(value))
    ? (value as ArtifactKind)
    : "response";
}

function validBrowserAction(value: unknown): TestStepRow["operationAction"] {
  return ["goto", "click", "fill", "wait", "screenshot"].includes(String(value))
    ? (value as TestStepRow["operationAction"])
    : "";
}
