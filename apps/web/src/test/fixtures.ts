import type { ProjectResponse, RunResponse } from "@warmy/generated-api-client";

export function projectFixture(
  overrides: Partial<ProjectResponse> = {},
): ProjectResponse {
  const archived = overrides.archived ?? false;
  return {
    archived,
    created_at: "2026-07-16T08:00:00Z",
    created_by: "user-1",
    description: null,
    id: "project-1",
    key: "PRJ001",
    lead_user_id: null,
    name: "项目 A",
    status: archived ? "archived" : "active",
    updated_at: "2026-07-16T08:00:00Z",
    updated_by: "user-1",
    ...overrides,
  };
}

export function runFixture(overrides: Partial<RunResponse> = {}): RunResponse {
  return {
    cancelled_cases: 0,
    completed_at: null,
    created_at: "2026-07-16T08:00:00Z",
    error_cases: 0,
    failed_cases: 0,
    id: "run-1",
    passed_cases: 0,
    project_id: "project-1",
    run_number: "RUN-0001",
    run_type: "plan",
    source_test_case_id: null,
    started_at: null,
    status: "queued",
    test_plan_version_id: "plan-version-1",
    total_cases: 1,
    workflow_id: null,
    ...overrides,
  };
}
