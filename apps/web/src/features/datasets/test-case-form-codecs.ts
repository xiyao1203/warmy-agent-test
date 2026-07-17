export type KeyValueRow = { id: string; key: string; value: string };
export type AssertionRow = {
  id: string;
  raw: Record<string, unknown>;
  type: string;
  path: string;
  value: string;
};
export type ScorerRow = {
  id: string;
  raw: Record<string, unknown>;
  name: string;
  type: string;
  threshold: string;
};
export type SecurityPolicyRow = {
  id: string;
  raw: Record<string, unknown>;
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
    raw: { ...assertion },
    type: formatCellValue(assertion.type ?? "contains"),
    path: formatCellValue(assertion.path ?? ""),
    value: formatCellValue(assertion.value ?? ""),
  }));
}

export function rowsToAssertions(rows: AssertionRow[]) {
  return rows
    .filter(
      (row) =>
        Object.keys(row.raw).length > 0 ||
        Boolean(row.path.trim() || row.value.trim()),
    )
    .map((row) => {
      const assertion: Record<string, unknown> = {
        ...row.raw,
        type: row.type.trim() || "contains",
      };
      if (row.path.trim()) assertion.path = row.path.trim();
      else delete assertion.path;
      if (row.value.trim()) assertion.value = parseCellValue(row.value);
      else delete assertion.value;
      return assertion;
    });
}

export function scorersToRows(
  scorers: Array<Record<string, unknown>>,
): ScorerRow[] {
  return scorers.map((scorer) => ({
    id: newFormRowId(),
    raw: { ...scorer },
    name: formatCellValue(scorer.name ?? ""),
    type: formatCellValue(scorer.type ?? "llm_judge"),
    threshold: formatCellValue(scorer.threshold ?? ""),
  }));
}

export function rowsToScorers(rows: ScorerRow[]) {
  return rows
    .filter(
      (row) => Object.keys(row.raw).length > 0 || Boolean(row.name.trim()),
    )
    .map((row) => {
      const scorer: Record<string, unknown> = {
        ...row.raw,
        type: row.type.trim() || "llm_judge",
      };
      if (row.name.trim()) scorer.name = row.name.trim();
      else delete scorer.name;
      if (row.threshold.trim()) scorer.threshold = Number(row.threshold);
      else delete scorer.threshold;
      return scorer;
    });
}

export function securityPoliciesToRows(
  policies: Array<Record<string, unknown>>,
): SecurityPolicyRow[] {
  return policies.map((policy) => ({
    id: newFormRowId(),
    raw: { ...policy },
    type: formatCellValue(policy.type ?? ""),
    severity: formatCellValue(policy.severity ?? "medium"),
  }));
}

export function rowsToSecurityPolicies(rows: SecurityPolicyRow[]) {
  return rows
    .filter(
      (row) => Object.keys(row.raw).length > 0 || Boolean(row.type.trim()),
    )
    .map((row) => {
      const policy: Record<string, unknown> = {
        ...row.raw,
        type: row.type.trim(),
      };
      if (!policy.type) delete policy.type;
      if (row.severity.trim()) policy.severity = row.severity.trim();
      else delete policy.severity;
      return policy;
    });
}
