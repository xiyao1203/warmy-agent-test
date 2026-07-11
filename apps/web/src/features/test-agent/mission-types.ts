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
};

export type MissionProgressOutput = {
  mission_id: string;
  status: string;
  workflow_id?: string;
  run_id?: string;
  missing_fields?: string[];
};
