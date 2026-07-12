export type MissionFact = {
  value: unknown;
  source:
    | "user_provided"
    | "platform_resolved"
    | "target_discovered"
    | "system_inferred";
  confidence: number;
  verified: boolean;
  sensitive: boolean;
};

export type TestMissionResponse = {
  mission_id: string;
  project_id: string;
  session_id: string;
  status: string;
  active_revision_id: string | null;
  workflow_id: string | null;
  facts: Record<string, MissionFact>;
  ready: boolean;
  missing_inputs: Array<{ key: string; reason: string }>;
  execution_channels: string[];
  action_allowlist: string[];
  inferred_scenarios: string[];
  revision_hash: string | null;
  snapshot: Record<string, unknown> | null;
  updated_at: string;
  assets?: Array<{
    type: string;
    id: string;
    relation: string;
    stage?: string | null;
  }>;
};

export type MissionProgressOutput = {
  mission_id: string;
  status: string;
  workflow_id?: string;
  run_id?: string;
  missing_fields?: string[];
  trust_loop?: TrustLoopResultData;
};

export type TrustOutcome = {
  status: "not_evaluated" | "passed" | "failed" | "error" | "needs_review";
  code: string;
  reason?: string;
  evidence_ids: string[];
};

export type TrustLoopResultData = {
  outcomes: {
    execution: TrustOutcome;
    assertion: TrustOutcome;
    quality: TrustOutcome;
    security: TrustOutcome;
  };
  diagnostics: Array<{
    summary: string;
    confidence: number;
    evidence_ids: string[];
  }>;
  regressions: Array<{ id: string; state: string; fingerprint: string }>;
  gate: {
    status: "allow" | "block" | "needs_review";
    rules: Array<{
      code: string;
      status: string;
      threshold: string;
      actual: string;
      reason: string;
      evidence_refs: string[];
    }>;
  };
};
