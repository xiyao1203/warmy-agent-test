export type KeyValueRow = { id: string; key: string; value: string };
export type AssertionRow = {
  id: string;
  type: string;
  path: string;
  value: string;
};
export type ScorerRow = {
  id: string;
  name: string;
  type: string;
  threshold: string;
};
export type SecurityPolicyRow = {
  id: string;
  type: string;
  severity: string;
};

export function newFormRowId() {
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

export function recordToRows(record: Record<string, unknown>): KeyValueRow[] {
  return Object.entries(record).map(([key, value]) => ({
    id: newFormRowId(),
    key,
    value: formatCellValue(value),
  }));
}

export function rowsToRecord(rows: KeyValueRow[]) {
  return Object.fromEntries(
    rows
      .filter((row) => row.key.trim())
      .map((row) => [row.key.trim(), parseCellValue(row.value)]),
  );
}

export function assertionsToRows(
  assertions: Array<Record<string, unknown>>,
): AssertionRow[] {
  return assertions.map((assertion) => ({
    id: newFormRowId(),
    type: formatCellValue(assertion.type ?? "contains"),
    path: formatCellValue(assertion.path ?? ""),
    value: formatCellValue(assertion.value ?? ""),
  }));
}

export function rowsToAssertions(rows: AssertionRow[]) {
  return rows
    .filter((row) => row.path.trim() || row.value.trim())
    .map((row) => ({
      type: row.type.trim() || "contains",
      path: row.path.trim(),
      value: parseCellValue(row.value),
    }));
}

export function scorersToRows(
  scorers: Array<Record<string, unknown>>,
): ScorerRow[] {
  return scorers.map((scorer) => ({
    id: newFormRowId(),
    name: formatCellValue(scorer.name ?? ""),
    type: formatCellValue(scorer.type ?? "llm_judge"),
    threshold: formatCellValue(scorer.threshold ?? ""),
  }));
}

export function rowsToScorers(rows: ScorerRow[]) {
  return rows
    .filter((row) => row.name.trim())
    .map((row) => ({
      name: row.name.trim(),
      type: row.type.trim() || "llm_judge",
      threshold: row.threshold.trim() ? Number(row.threshold) : undefined,
    }));
}

export function securityPoliciesToRows(
  policies: Array<Record<string, unknown>>,
): SecurityPolicyRow[] {
  return policies.map((policy) => ({
    id: newFormRowId(),
    type: formatCellValue(policy.type ?? ""),
    severity: formatCellValue(policy.severity ?? "medium"),
  }));
}

export function rowsToSecurityPolicies(rows: SecurityPolicyRow[]) {
  return rows
    .filter((row) => row.type.trim())
    .map((row) => ({
      type: row.type.trim(),
      severity: row.severity.trim() || "medium",
    }));
}
