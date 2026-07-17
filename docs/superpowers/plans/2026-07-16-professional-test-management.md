# Professional Test Management Implementation Plan

**Status:** Completed on 2026-07-16. Verification evidence is recorded in `docs/开发进度与变更记录.md` under `TASK-20260716-001`; unchecked step boxes below preserve the original execution plan rather than live task state.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build one professional test-case contract shared by manual forms, AI generation, imports, plans and execution, while enriching every core platform list with decision-ready cross-resource data.

**Architecture:** The Datasets module owns PlatformTestCaseV1 and publishes typed application contracts. Projects and Datasets receive additive PostgreSQL migrations and deterministic backfills; Runs persist secret-free immutable snapshots; Test Agent consumes module public APIs. Core list pages use application Summary DTOs and bounded aggregate reads, while the Web app renders the generated OpenAPI types through feature-local forms and tables.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL JSONB, Temporal, pytest, Next.js 16.2.9, React 19, TypeScript, Vitest, Testing Library, Playwright, generated OpenAPI client.

---

## File map

New backend files:

- apps/control-api/migrations/versions/0027_professional_test_management.py: additive schema, deterministic backfill, constraints and indexes.
- apps/control-api/src/agenttest/modules/datasets/application/contracts.py: PlatformTestCaseV1, TestStepV1, DataBindingV1, ArtifactRequirementV1 and validation issues.
- apps/control-api/src/agenttest/modules/datasets/application/trial_runs.py: validate and create an immutable single-case trial run.
- apps/control-api/src/agenttest/shared/application/resource_reference.py: safe cross-module ResourceReference DTO.
- apps/control-api/tests/unit/datasets/test_professional_case_contract.py: canonical contract invariants.
- apps/control-api/tests/integration/test_professional_asset_migration.py: migration, backfill, sequence and project-isolation evidence.
- apps/control-api/tests/unit/datasets/test_trial_run.py: single-case run creation and secret-free snapshot.
- apps/control-api/tests/unit/test_agent/test_professional_case_capabilities.py: Agent Schema and resource-result contract.
- apps/control-api/tests/performance/test_core_list_query_budgets.py: N+1 budgets for all summary reads.

New frontend files:

- apps/web/src/features/datasets/test-case-professional-fields.ts: form types, defaults and generated-client conversions.
- apps/web/src/features/datasets/test-case-step-editor.tsx: ordered action, data, expected-result, assertion and artifact editor.
- apps/web/src/features/datasets/test-case-data-bindings.tsx: typed and secret-safe data source editor.
- apps/web/src/features/datasets/test-case-validation.tsx: readiness issue display.
- apps/web/src/features/datasets/test-case-trial-run.tsx: Agent/environment selection and result entry point.
- apps/web/src/components/ui/resource-reference-link.tsx: typed internal resource link.
- apps/web/src/features/datasets/tests/test-case-professional-form.test.tsx: manual form and AI draft round trip.
- apps/web/tests/e2e/professional-test-management.spec.ts: full form, list and cross-resource journey.

Existing backend files with direct responsibilities:

- projects domain, commands, query, schemas, router, persistence models/repositories and public export.
- datasets domain, commands, queries, import/export, schemas, router, models/repositories and public export.
- runs domain, commands, queries, execution_snapshot, schemas, router, models/repositories, orchestrator and public export.
- test_agent platform_catalog and platform adapter.
- agents, test_plans, environments, scorers, experiments, security, reviews and gates query/service, API and persistence files.
- bootstrap module registrars that construct the added handlers.
- workers/api-runner contracts, activities, browser/codex activities and workflow.

Existing frontend files with direct responsibilities:

- projects/project-list-screen.tsx.
- datasets/dataset-list.tsx, dataset-detail.tsx, test-case-editor.tsx, test-case-editors.tsx, test-case-form-codecs.ts and api.ts.
- agents/agent-list.tsx.
- test-plans/test-plan-list.tsx.
- runs/run-center.tsx.
- environments/environment-list.tsx.
- scorers/scorer-list.tsx.
- experiments/experiment-list.tsx.
- security/security-scan.tsx.
- reviews/review-workbench.tsx.
- gates/gate-list.tsx.
- each corresponding feature test and public index.

## Task 1: Canonical professional test-case contract

**Files:**

- Create: apps/control-api/src/agenttest/modules/datasets/application/contracts.py
- Modify: apps/control-api/src/agenttest/modules/datasets/domain/value_objects.py
- Modify: apps/control-api/src/agenttest/modules/datasets/domain/entities.py
- Modify: apps/control-api/src/agenttest/modules/datasets/application/commands.py
- Modify: apps/control-api/src/agenttest/modules/datasets/public.py
- Test: apps/control-api/tests/unit/datasets/test_professional_case_contract.py
- Test: apps/control-api/tests/unit/datasets/test_dataset_domain.py

- [ ] **Step 1: Write failing contract tests**

Add tests that construct a step-by-step case, reject a missing expected result, reject a sensitive literal binding, normalize step numbers, require an oracle before ready, and serialize the contract without losing fields.

    def test_step_by_step_case_requires_professional_steps() -> None:
        with pytest.raises(ValueError, match="expected_result"):
            PlatformTestCaseV1(
                name="Login",
                objective="Verify login",
                input={"email": "qa@example.test"},
                template=TestCaseTemplate.STEP_BY_STEP,
                execution_mode=ExecutionMode.BROWSER,
                steps=[TestStepV1(step_no=7, action="Submit login", expected_result="")],
            )

    def test_sensitive_binding_must_reference_secret() -> None:
        with pytest.raises(ValueError, match="reference"):
            DataBindingV1(
                name="password",
                source=DataBindingSource.CREDENTIAL,
                value="plain-secret",
                sensitive=True,
            )

    def test_ready_case_requires_machine_or_semantic_oracle() -> None:
        draft = professional_case(case_status=TestCaseStatus.DRAFT)
        with pytest.raises(ValueError, match="oracle"):
            draft.mark_ready()

- [ ] **Step 2: Run the tests and verify RED**

Run:

    uv run pytest apps/control-api/tests/unit/datasets/test_professional_case_contract.py -q

Expected: collection fails because the new contracts and enums do not exist.

- [ ] **Step 3: Implement enums and typed contracts**

Define:

    class TestCaseStatus(StrEnum):
        DRAFT = "draft"
        READY = "ready"
        DEPRECATED = "deprecated"

    class TestCaseTemplate(StrEnum):
        STEP_BY_STEP = "step_by_step"
        TEXT = "text"
        BDD = "bdd"
        AI_EVAL = "ai_eval"

    class TestCaseType(StrEnum):
        FUNCTIONAL = "functional"
        REGRESSION = "regression"
        SMOKE = "smoke"
        INTEGRATION = "integration"
        E2E = "e2e"
        SECURITY = "security"
        PERFORMANCE = "performance"
        USABILITY = "usability"
        EXPLORATORY = "exploratory"

    class AutomationStatus(StrEnum):
        MANUAL = "manual"
        CANDIDATE = "candidate"
        AUTOMATED = "automated"

    class TestCaseSource(StrEnum):
        MANUAL = "manual"
        AGENT_GENERATED = "agent_generated"
        IMPORTED = "imported"
        RUN_REGRESSION = "run_regression"

Implement frozen Pydantic contracts with bounded strings, arrays, custom_fields size/depth validation, contiguous step normalization and sensitive binding rules. Add to_application_fields() so API, import and Agent paths use one converter.

- [ ] **Step 4: Extend the TestCase domain and commands**

Add the professional fields to TestCase, AddTestCaseCommand and UpdateTestCaseCommand. TestCase.mark_ready() calls the shared validator, TestCase.deprecate() records the state transition, and TestCase.create() preserves current defaults for legacy callers:

    objective = objective.strip() if objective else normalized_name
    case_status = case_status or TestCaseStatus.DRAFT
    template = template or TestCaseTemplate.AI_EVAL
    automation_status = automation_status or AutomationStatus.AUTOMATED
    source = source or TestCaseSource.MANUAL

Update public.py to export only the application contracts, commands, IDs and enums needed by other modules.

- [ ] **Step 5: Run focused tests and static checks**

Run:

    uv run pytest apps/control-api/tests/unit/datasets/test_professional_case_contract.py apps/control-api/tests/unit/datasets/test_dataset_domain.py -q
    uv run ruff check apps/control-api/src/agenttest/modules/datasets apps/control-api/tests/unit/datasets
    uv run mypy apps/control-api/src/agenttest/modules/datasets

Expected: all commands exit 0.

- [ ] **Step 6: Commit**

    git add apps/control-api/src/agenttest/modules/datasets apps/control-api/tests/unit/datasets
    git commit -m "feat: define professional test case contract"

## Task 2: Project metadata, case numbering and persistence migration

**Files:**

- Create: apps/control-api/migrations/versions/0027_professional_test_management.py
- Modify: apps/control-api/src/agenttest/modules/projects/domain/entities.py
- Modify: apps/control-api/src/agenttest/modules/projects/domain/repositories.py
- Modify: apps/control-api/src/agenttest/modules/projects/application/commands/create_project.py
- Modify: apps/control-api/src/agenttest/modules/projects/infrastructure/persistence/models.py
- Modify: apps/control-api/src/agenttest/modules/projects/infrastructure/persistence/repositories.py
- Modify: apps/control-api/src/agenttest/modules/datasets/application/ports.py
- Modify: apps/control-api/src/agenttest/modules/datasets/application/commands.py
- Modify: apps/control-api/src/agenttest/modules/datasets/infrastructure/persistence/models.py
- Modify: apps/control-api/src/agenttest/modules/datasets/infrastructure/persistence/repositories.py
- Modify: the datasets and projects bootstrap registrars that wire repositories and handlers
- Test: apps/control-api/tests/integration/test_professional_asset_migration.py
- Test: apps/control-api/tests/contract/test_projects_api.py
- Test: apps/control-api/tests/contract/test_datasets_api.py

- [ ] **Step 1: Write failing migration and concurrency tests**

Cover:

- empty database upgrade to head;
- upgrade from 0026 with old projects and test_cases;
- deterministic non-empty unique project keys and case keys;
- next allocated case number follows backfilled maximum;
- eight concurrent allocations return eight distinct values;
- project key is immutable;
- owner and lead references are project-valid.

    values = await asyncio.gather(
        *(allocator.next_value(project_id, "test_case") for _ in range(8))
    )
    assert sorted(values) == list(range(min(values), min(values) + 8))
    assert len(set(values)) == 8

- [ ] **Step 2: Run PostgreSQL tests and verify RED**

Run the repository PostgreSQL test command with AGENTTEST_TEST_DATABASE_URL set to an isolated disposable database, targeting the new test file.

Expected: migration revision 0027 and allocator do not exist.

- [ ] **Step 3: Implement migration 0027**

Add projects.key and projects.lead_user_id, project_sequences, and all professional test_cases fields from the approved design. Backfill keys with SQL based on stable UUID text and row_number partitioned by project. Add:

- unique projects.key;
- unique test_cases.case_key;
- unique project_sequences(project_id, resource_type);
- checks for project key format, enum values, duration, timeout and retry ranges;
- indexes for project key, case key, case status/type/automation and updated_at;
- user foreign keys for lead_user_id, owner_id, created_by and updated_by.

The migration must never rewrite input, assertions, scorers or security_policies.

- [ ] **Step 4: Implement project mapping and atomic sequence repository**

Map description, key, lead, creator/updater and timestamps into the Project domain. Generate an omitted key from name plus a stable UUID suffix. Implement:

    INSERT INTO project_sequences(project_id, resource_type, next_value)
    VALUES (:project_id, :resource_type, 2)
    ON CONFLICT (project_id, resource_type)
    DO UPDATE SET next_value = project_sequences.next_value + 1
    RETURNING next_value - 1

Expose this through CaseKeyAllocatorPort and format case keys as project-key-TC-six-digit-number.

- [ ] **Step 5: Map every professional case field**

Update TestCaseModel, repository add/save and _to_test_case. Add created_by and updated_by to command handlers and audit only field names and resource IDs, never sensitive values.

- [ ] **Step 6: Run focused tests**

Run:

    uv run pytest apps/control-api/tests/unit/projects apps/control-api/tests/unit/datasets -q

Then run the isolated PostgreSQL migration suite including test_professional_asset_migration.py.

Expected: unit and PostgreSQL tests exit 0 with no skipped assertions in the new migration file.

- [ ] **Step 7: Commit**

    git add apps/control-api/migrations/versions/0027_professional_test_management.py apps/control-api/src/agenttest/modules/projects apps/control-api/src/agenttest/modules/datasets apps/control-api/tests/integration/test_professional_asset_migration.py apps/control-api/tests/unit/projects apps/control-api/tests/unit/datasets
    git commit -m "feat: persist professional project and case metadata"

## Task 3: Professional case API, validation and import/export

**Files:**

- Modify: apps/control-api/src/agenttest/modules/datasets/api/schemas.py
- Modify: apps/control-api/src/agenttest/modules/datasets/api/router.py
- Modify: apps/control-api/src/agenttest/modules/datasets/application/commands.py
- Modify: apps/control-api/src/agenttest/modules/datasets/application/queries.py
- Modify: apps/control-api/src/agenttest/modules/datasets/application/import_export.py
- Modify: apps/control-api/src/agenttest/modules/datasets/application/generate_from_run.py
- Modify: bootstrap dataset registrar
- Test: apps/control-api/tests/contract/test_datasets_api.py
- Test: apps/control-api/tests/contract/test_dataset_import_preview_api.py
- Test: apps/control-api/tests/unit/datasets/test_import_contract.py
- Test: apps/control-api/tests/unit/datasets/test_generate_from_run.py

- [ ] **Step 1: Write failing API and round-trip tests**

Create a full case through HTTP, read it back, patch steps, validate it, mark it ready, duplicate it, export/import JSON and confirm every professional field survives. Add rejection cases for missing expected_result, oversized custom_fields, plaintext credential data and cross-project owner.

    response = client.post(case_url, json=professional_case_payload())
    assert response.status_code == 201
    assert response.json()["steps"][0] == {
        "step_no": 1,
        "action": "Send request",
        "test_data": {"message": "hello"},
        "expected_result": "Agent returns a greeting",
        "assertions": [],
        "artifact_requirements": [],
    }

- [ ] **Step 2: Verify RED**

Run:

    uv run pytest apps/control-api/tests/contract/test_datasets_api.py apps/control-api/tests/contract/test_dataset_import_preview_api.py apps/control-api/tests/unit/datasets/test_import_contract.py -q

Expected: new response fields and actions are missing.

- [ ] **Step 3: Make API schemas use PlatformTestCaseV1**

Create request models from the shared nested contracts, keep existing input/assertions fields, and add TestCaseValidationIssue and TestCaseValidationResponse. TestCaseResponse.from_domain returns all fields exactly once.

Add routes:

- POST cases/{case_id}/validate;
- POST cases/{case_id}/mark-ready;
- POST cases/{case_id}/duplicate.

Every route first resolves project, dataset, version and case using existing scoped helpers.

- [ ] **Step 4: Upgrade import/export**

Extend required/optional fields and Chinese aliases. Complex CSV values parse as JSON with field-level errors. Export the complete V1 contract. Source is forced to imported for new imported records; source_ref stores an opaque import batch identifier, not a filename containing user secrets.

- [ ] **Step 5: Upgrade run-regression generation**

Generated regression cases set source run_regression, source_ref to the Run resource ID, objective from the failure diagnosis, expected_outcome from the observed contract and at least one deterministic assertion.

- [ ] **Step 6: Run focused tests and API drift generation**

Run:

    uv run pytest apps/control-api/tests/contract/test_datasets_api.py apps/control-api/tests/contract/test_dataset_import_preview_api.py apps/control-api/tests/unit/datasets -q
    make api

Expected: tests pass and the OpenAPI document includes all nested professional fields and actions.

- [ ] **Step 7: Commit**

    git add apps/control-api/src/agenttest/modules/datasets apps/control-api/tests/contract/test_datasets_api.py apps/control-api/tests/contract/test_dataset_import_preview_api.py apps/control-api/tests/unit/datasets openapi packages/generated-api-client
    git commit -m "feat: expose professional test case api"

## Task 4: Immutable single-case trial execution

**Files:**

- Create: apps/control-api/src/agenttest/modules/datasets/application/trial_runs.py
- Modify: apps/control-api/src/agenttest/modules/runs/domain/value_objects.py
- Modify: apps/control-api/src/agenttest/modules/runs/domain/entities.py
- Modify: apps/control-api/src/agenttest/modules/runs/application/commands.py
- Modify: apps/control-api/src/agenttest/modules/runs/application/execution_snapshot.py
- Modify: apps/control-api/src/agenttest/modules/runs/api/schemas.py
- Modify: apps/control-api/src/agenttest/modules/runs/api/router.py
- Modify: apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/models.py
- Modify: apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/repositories.py
- Modify: apps/control-api/migrations/versions/0027_professional_test_management.py before it is released
- Modify: run and dataset bootstrap registrars
- Test: apps/control-api/tests/unit/datasets/test_trial_run.py
- Test: apps/control-api/tests/unit/runs/test_execution_snapshot.py
- Test: apps/control-api/tests/integration/test_run_execution_snapshot.py
- Test: apps/control-api/tests/contract/test_runs_api.py

- [ ] **Step 1: Write failing trial-run tests**

Cover project isolation, Agent/environment validation, idempotency, no empty Run after validation failure, snapshot completeness, plaintext-secret absence and exclusion from formal pass-rate aggregates.

    result = await handler.execute(
        actor,
        CreateCaseTrialRunCommand(
            project_id=project_id,
            case_id=case.case_id,
            agent_version_id=agent_version_id,
            environment_template_id=environment_id,
            idempotency_key="trial-1",
        ),
    )
    snapshot = result.run_cases[0].case_spec_snapshot
    assert snapshot["case_key"] == case.case_key
    assert snapshot["steps"][0]["action"] == "Send prompt"
    assert "plain-secret" not in json.dumps(snapshot)

- [ ] **Step 2: Verify RED**

Run:

    uv run pytest apps/control-api/tests/unit/datasets/test_trial_run.py apps/control-api/tests/unit/runs/test_execution_snapshot.py -q

Expected: trial command, run_type and case_spec_snapshot are missing.

- [ ] **Step 3: Add run_type and source case persistence**

Add run_type plan or case_trial, nullable test_plan_version_id for case_trial, source_test_case_id and full case_spec_snapshot. Database checks enforce:

- plan run has test_plan_version_id;
- case_trial has source_test_case_id and no plan requirement;
- both remain project scoped.

- [ ] **Step 4: Implement trial handler and route**

Add POST cases/{case_id}/trial-runs with agent_version_id, environment_template_id and idempotency key. The handler validates the V1 case, resolves same-project immutable references, compiles the snapshot, creates one RunCase and schedules through the existing orchestrator.

- [ ] **Step 5: Update execution snapshot compiler**

Plan runs and case trials both produce:

    {
        "schema_version": "platform-test-case/v1",
        "case_key": case.case_key,
        "objective": case.objective,
        "preconditions": case.preconditions,
        "input": case.input,
        "data_bindings": secret_free_bindings,
        "steps": serialized_steps,
        "expected_outcome": case.expected_outcome,
        "assertions": case.assertions,
        "scorers": case.scorers,
        "security_policies": case.security_policies,
        "artifact_requirements": serialized_requirements,
        "postconditions": case.postconditions,
        "execution_mode": case.execution_mode.value,
    }

- [ ] **Step 6: Run focused unit, contract and PostgreSQL tests**

Run the four test files listed for this task, including the isolated PostgreSQL integration test.

Expected: all exit 0 and snapshots contain no credential values.

- [ ] **Step 7: Commit**

    git add apps/control-api/migrations/versions/0027_professional_test_management.py apps/control-api/src/agenttest/modules/datasets apps/control-api/src/agenttest/modules/runs apps/control-api/tests/unit/datasets/test_trial_run.py apps/control-api/tests/unit/runs/test_execution_snapshot.py apps/control-api/tests/integration/test_run_execution_snapshot.py apps/control-api/tests/contract/test_runs_api.py
    git commit -m "feat: add immutable single case trial runs"

## Task 5: Worker consumption of the V1 snapshot

**Files:**

- Modify: workers/api-runner/src/agenttest_api_runner/contracts.py
- Modify: workers/api-runner/src/agenttest_api_runner/activities.py
- Modify: workers/api-runner/src/agenttest_api_runner/playwright_activity.py
- Modify: workers/api-runner/src/agenttest_api_runner/browser_harness_activity.py
- Modify: workers/api-runner/src/agenttest_api_runner/codex_browser_activity.py
- Modify: workers/api-runner/src/agenttest_api_runner/workflow.py
- Test: workers/api-runner/tests/test_invocation_contract.py
- Test: workers/api-runner/tests/test_protocol_execution.py
- Test: workers/api-runner/tests/test_browser_harness_activity.py
- Test: workers/api-runner/tests/test_workflow.py

- [ ] **Step 1: Write failing snapshot-consumption tests**

API tests assert input and top-level oracles are preserved. Browser tests assert ordered steps, per-step expected results and artifact requirements reach the harness. Codex tests assert objective and safety policy bound exploration. All modes assert postconditions cannot introduce unapproved high-risk actions.

- [ ] **Step 2: Verify RED**

Run:

    uv run pytest workers/api-runner/tests/test_invocation_contract.py workers/api-runner/tests/test_protocol_execution.py workers/api-runner/tests/test_browser_harness_activity.py workers/api-runner/tests/test_workflow.py -q

Expected: contracts ignore V1 fields.

- [ ] **Step 3: Add typed worker contracts**

Introduce PlatformTestCaseSnapshotV1 and nested models. Parse schema_version explicitly. Keep a legacy parser for already-started Workflow histories, but all new runs must emit V1.

- [ ] **Step 4: Compile per execution mode**

- API uses input and request template, then applies top-level and step assertions.
- Browser converts each TestStepV1 into harness instruction, preserving order and evidence requirements.
- Codex combines objective, preconditions, steps, expected outcome and safety scope without allowing the model to widen actions.

Postcondition cleanup is limited to explicitly supported safe actions.

- [ ] **Step 5: Run worker tests and static checks**

Run:

    uv run pytest workers/api-runner/tests -q
    uv run ruff check workers/api-runner
    uv run mypy workers/api-runner/src

Expected: all commands exit 0.

- [ ] **Step 6: Commit**

    git add workers/api-runner
    git commit -m "feat: execute professional case snapshots"

## Task 6: Test Agent professional capabilities

**Files:**

- Modify: apps/control-api/src/agenttest/modules/test_agent/application/platform_catalog.py
- Modify: apps/control-api/src/agenttest/modules/test_agent/adapters/platform.py
- Modify: apps/control-api/src/agenttest/modules/test_agent/application/sub_agents.py
- Modify: apps/control-api/src/agenttest/modules/test_agent/application/model_planner.py
- Modify: apps/control-api/src/agenttest/modules/datasets/public.py
- Test: apps/control-api/tests/unit/test_agent/test_platform_capability_catalog.py
- Test: apps/control-api/tests/unit/test_agent/test_platform_dataset_cases.py
- Create: apps/control-api/tests/unit/test_agent/test_professional_case_capabilities.py

- [ ] **Step 1: Write failing catalog and generation tests**

Assert test_cases list/get/create/update/validate/mark_ready/trial_run exist with correct risk levels. Mock the model returning a full professional case and confirm every field reaches AddTestCaseCommand. Return an invalid step and assert a structured validation error with no dataset committed.

- [ ] **Step 2: Verify RED**

Run:

    uv run pytest apps/control-api/tests/unit/test_agent/test_platform_capability_catalog.py apps/control-api/tests/unit/test_agent/test_platform_dataset_cases.py apps/control-api/tests/unit/test_agent/test_professional_case_capabilities.py -q

Expected: new capabilities and typed case input are missing.

- [ ] **Step 3: Replace TestCaseDraftInput with the shared V1 input**

The capability model references the Datasets public schema instead of duplicating fields. auto_generate_cases asks for objective, professional preparation, input, ordered steps, per-step expected results, assertions/scorers/security, classification and source metadata.

Validate parsed model output with:

    validated_cases = TypeAdapter(list[PlatformTestCaseV1]).validate_python(cases)

Set source to agent_generated and source_ref to the generation/session resource regardless of model-provided provenance.

- [ ] **Step 4: Add capability handlers and rich results**

Add scoped list/get/create/update/validate/mark-ready/trial-run handlers. Replace minimal artifact payloads with ResourceReference and validation metadata. HIGH_IMPACT remains required for publish and execution.

- [ ] **Step 5: Run tests and architecture boundaries**

Run:

    uv run pytest apps/control-api/tests/unit/test_agent -q
    uv run pytest apps/control-api/tests/architecture -q
    python scripts/check_architecture.py

Expected: all commands exit 0 and Test Agent imports only module public contracts.

- [ ] **Step 6: Commit**

    git add apps/control-api/src/agenttest/modules/test_agent apps/control-api/src/agenttest/modules/datasets/public.py apps/control-api/tests/unit/test_agent
    git commit -m "feat: connect test agent to professional cases"

## Task 7: Project and primary asset summary APIs

**Files:**

- Create: apps/control-api/src/agenttest/shared/application/resource_reference.py
- Modify: projects queries, schemas, router and repositories
- Modify: agents queries, schemas, router and repositories
- Modify: datasets queries, schemas, router and repositories
- Modify: test_plans queries, schemas, router and repositories
- Modify: runs queries, schemas, router and repositories
- Modify: environments queries, schemas, router and repositories
- Modify: each affected module public.py and bootstrap registrar
- Test: contract tests for projects, agents, datasets, plans, runs and environments
- Create: apps/control-api/tests/performance/test_core_list_query_budgets.py

- [ ] **Step 1: Write failing response and SQL-budget tests**

For each primary list, assert the approved default decision fields and ResourceReference objects. Seed at least three rows and assert query count is constant as row count increases.

    small = await measure_queries(lambda: list_agents(project_id, seeded=1))
    large = await measure_queries(lambda: list_agents(project_id, seeded=25))
    assert large <= small + 1

- [ ] **Step 2: Verify RED**

Run the six contract tests and test_core_list_query_budgets.py.

Expected: summary fields and resource references are missing.

- [ ] **Step 3: Implement ResourceReference**

Use an enum allowlist for resource_type and route-name mapping. The DTO contains id, key, name, version, status and href. Never accept href from a model, database JSON or external target.

- [ ] **Step 4: Implement bounded Summary DTO queries**

Add project-scoped collection queries for:

- ProjectSummary: member and asset counts plus latest run.
- AgentSummary: current version, protocol/model/tools/credentials, connection and run outcome.
- DatasetSummary: latest version, case readiness and execution-mode distribution.
- TestPlanSummary: linked resources, execution config and latest run.
- RunSummary: linked resources, run type, progress, outcomes, duration and cost.
- EnvironmentSummary: version, binding/browser profile, validation and last usage.

Use SQL joins/subqueries in Infrastructure and return typed application rows. Keep API free of SQLAlchemy.

- [ ] **Step 5: Run contract, isolation and performance tests**

Run:

    uv run pytest apps/control-api/tests/contract/test_projects_api.py apps/control-api/tests/contract/test_agents_api.py apps/control-api/tests/contract/test_datasets_api.py apps/control-api/tests/contract/test_test_plans_api.py apps/control-api/tests/contract/test_runs_api.py apps/control-api/tests/contract/test_environments_api.py -q
    uv run pytest apps/control-api/tests/performance/test_core_list_query_budgets.py apps/control-api/tests/integration/projects/test_project_isolation.py -q

Expected: all commands exit 0; PostgreSQL-backed budgets are explicitly run in the isolated database phase if unavailable on the default SQLite test path.

- [ ] **Step 6: Commit**

    git add apps/control-api/src/agenttest/shared/application/resource_reference.py apps/control-api/src/agenttest/modules/projects apps/control-api/src/agenttest/modules/agents apps/control-api/src/agenttest/modules/datasets apps/control-api/src/agenttest/modules/test_plans apps/control-api/src/agenttest/modules/runs apps/control-api/src/agenttest/modules/environments apps/control-api/tests/contract apps/control-api/tests/performance/test_core_list_query_budgets.py apps/control-api/tests/integration/projects/test_project_isolation.py
    git commit -m "feat: add decision ready primary asset summaries"

## Task 8: Quality, security and governance summary APIs

**Files:**

- Modify: scorers application/service, API router and repository
- Modify: experiments application/service, API router and repository
- Modify: security application/scan_service, API scan_router and repository
- Modify: reviews application/service, API router and repository
- Modify: gates application/service, API router and repository
- Modify: corresponding public exports and bootstrap wiring
- Test: apps/control-api/tests/unit/scorers/test_service.py
- Test: apps/control-api/tests/unit/experiments/test_service.py
- Test: apps/control-api/tests/unit/security/test_service.py
- Test: apps/control-api/tests/unit/reviews/test_service.py
- Test: apps/control-api/tests/unit/gates/test_service.py
- Test: apps/control-api/tests/integration/test_experiment_review_chain.py
- Test: apps/control-api/tests/integration/test_security_asset_chain.py

- [ ] **Step 1: Write failing summary tests**

Assert:

- scorer version, threshold, status, usage and calibration;
- experiment baseline/candidate references and deltas;
- scan target/profile references and severity counts;
- review run/case references, reason, priority, assignee and age;
- gate scope, rule summary, latest decision and blockers.

Also assert every referenced asset is from the requested project.

- [ ] **Step 2: Verify RED**

Run the listed unit and integration tests.

Expected: approved summary fields are absent.

- [ ] **Step 3: Implement typed summary services**

Add repository projection methods that aggregate by project and resource IDs. Compute duration and age from stored timestamps, not browser time. Return null for unavailable calibration/cost data rather than zero.

- [ ] **Step 4: Return ResourceReference in APIs and Agent gateway**

Update routes and the platform adapter mapping helpers so UI lists and Test Agent receive the same summaries. Gate hrefs use the allowlisted route mapper.

- [ ] **Step 5: Run focused tests and query budgets**

Run:

    uv run pytest apps/control-api/tests/unit/scorers apps/control-api/tests/unit/experiments apps/control-api/tests/unit/security apps/control-api/tests/unit/reviews apps/control-api/tests/unit/gates apps/control-api/tests/integration/test_experiment_review_chain.py apps/control-api/tests/integration/test_security_asset_chain.py -q
    uv run pytest apps/control-api/tests/performance/test_core_list_query_budgets.py -q

Expected: all commands exit 0.

- [ ] **Step 6: Commit**

    git add apps/control-api/src/agenttest/modules/scorers apps/control-api/src/agenttest/modules/experiments apps/control-api/src/agenttest/modules/security apps/control-api/src/agenttest/modules/reviews apps/control-api/src/agenttest/modules/gates apps/control-api/src/agenttest/modules/test_agent/adapters/platform.py apps/control-api/tests/unit apps/control-api/tests/integration apps/control-api/tests/performance/test_core_list_query_budgets.py
    git commit -m "feat: enrich quality and governance summaries"

## Task 9: Regenerate and lock API client contracts

**Files:**

- Modify: openapi/control-api.json
- Modify: packages/generated-api-client/src/generated/**
- Modify: generated client contract snapshots/tests

- [ ] **Step 1: Generate OpenAPI and client**

Run:

    make api

Expected: generated schemas include ProjectSummary, PlatformTestCaseV1 nested fields, trial runs, ResourceReference and all module summaries.

- [ ] **Step 2: Run generated client checks**

Run:

    make api-check
    pnpm --filter @warmy/generated-api-client typecheck
    pnpm --filter @warmy/generated-api-client test

Expected: no drift, type errors or failed tests.

- [ ] **Step 3: Commit**

    git add openapi packages/generated-api-client
    git commit -m "chore: regenerate professional management api client"

## Task 10: Professional manual case form

**Files:**

- Create: apps/web/src/features/datasets/test-case-professional-fields.ts
- Create: apps/web/src/features/datasets/test-case-step-editor.tsx
- Create: apps/web/src/features/datasets/test-case-data-bindings.tsx
- Create: apps/web/src/features/datasets/test-case-validation.tsx
- Create: apps/web/src/features/datasets/test-case-trial-run.tsx
- Modify: apps/web/src/features/datasets/test-case-editor.tsx
- Modify: apps/web/src/features/datasets/test-case-editors.tsx
- Modify: apps/web/src/features/datasets/test-case-form-codecs.ts
- Modify: apps/web/src/features/datasets/test-case-format.ts
- Modify: apps/web/src/features/datasets/test-case-detail.tsx
- Modify: apps/web/src/features/datasets/dataset-detail.tsx
- Modify: apps/web/src/features/datasets/api.ts
- Modify: apps/web/src/features/datasets/index.ts
- Create: apps/web/src/features/datasets/tests/test-case-professional-form.test.tsx
- Modify: apps/web/src/features/datasets/tests/test-case-editor.test.tsx
- Modify: apps/web/src/features/datasets/tests/test-case-form-codecs.test.ts

- [ ] **Step 1: Write failing form tests**

Test manual creation of identity, objective, classification, preconditions, typed input, credential reference, two ordered steps, per-step expected results, assertions, postconditions and execution settings. Test editing an Agent-generated draft, reordering steps, inline validation, dirty navigation and published read-only behavior.

    await user.type(screen.getByLabelText("测试目标"), "验证客服 Agent 拒绝越权查询")
    await user.click(screen.getByRole("button", { name: "添加操作步骤" }))
    await user.type(screen.getByLabelText("步骤 1 操作"), "发送越权查询")
    await user.type(screen.getByLabelText("步骤 1 预期结果"), "拒绝并说明隐私限制")
    await user.click(screen.getByRole("button", { name: "保存草稿" }))
    expect(createTestCase).toHaveBeenCalledWith(
        expect.objectContaining({
            objective: "验证客服 Agent 拒绝越权查询",
            steps: [expect.objectContaining({ step_no: 1 })],
        }),
    )

- [ ] **Step 2: Verify RED**

Run:

    pnpm --filter @warmy/web exec vitest run src/features/datasets/tests/test-case-professional-form.test.tsx src/features/datasets/tests/test-case-editor.test.tsx src/features/datasets/tests/test-case-form-codecs.test.ts

Expected: professional controls and codecs are missing.

- [ ] **Step 3: Implement form model and codecs**

Use generated API types as transport types and feature-local FormRow types only for stable React keys. Conversion functions must round-trip all fields and remove empty display rows without dropping legitimate false, zero or empty-object inputs.

- [ ] **Step 4: Implement accessible editors**

Split the dialog into the seven approved sections. Data bindings expose source, type and sensitive reference. Step editor supports add, copy, delete and move up/down with keyboard-accessible buttons; drag can be progressive enhancement but button ordering is required.

Every error connects through aria-describedby. Published versions render details and an “创建草稿版本后编辑” action instead of enabled inputs.

- [ ] **Step 5: Implement validation and trial run actions**

Save draft, validate, mark ready, add to plan and trial run call generated-client APIs. Trial run requires Agent version and environment selection, shows high-impact confirmation and links the returned Run resource.

- [ ] **Step 6: Run focused Web checks**

Run:

    pnpm --filter @warmy/web exec vitest run src/features/datasets/tests
    pnpm --filter @warmy/web lint
    pnpm --filter @warmy/web typecheck

Expected: all commands exit 0.

- [ ] **Step 7: Commit**

    git add apps/web/src/features/datasets
    git commit -m "feat: add professional test case form"

## Task 11: Enriched primary core lists and resource navigation

**Files:**

- Create: apps/web/src/components/ui/resource-reference-link.tsx
- Modify: apps/web/src/features/projects/project-list-screen.tsx
- Modify: apps/web/src/features/projects/api.ts
- Modify: apps/web/src/features/agents/agent-list.tsx
- Modify: apps/web/src/features/agents/api.ts
- Modify: apps/web/src/features/datasets/dataset-list.tsx
- Modify: apps/web/src/features/datasets/dataset-detail.tsx
- Modify: apps/web/src/features/test-plans/test-plan-list.tsx
- Modify: apps/web/src/features/runs/run-center.tsx
- Modify: apps/web/src/features/environments/environment-list.tsx
- Modify: corresponding feature index and tests

- [ ] **Step 1: Write failing table tests**

For every primary list, render the generated Summary payload and assert all approved default decision fields, links, status labels and null-state labels. Add 390 and 1280 layout assertions through the existing list E2E utilities.

- [ ] **Step 2: Verify RED**

Run the project, agent, dataset, plan, run and environment feature tests.

Expected: current shallow columns fail the assertions.

- [ ] **Step 3: Implement ResourceReferenceLink**

Render only allowlisted internal hrefs and fall back to a non-link label if href is unavailable. Include name, key/version secondary text and accessible resource type.

- [ ] **Step 4: Enrich the six primary lists**

Use generated Summary types directly. Defaults match the approved design; lower-priority fields appear in details or optional column configuration. Preserve existing TableActionButton, TruncatedText and single-DOM mobile layout.

- [ ] **Step 5: Run focused tests**

Run:

    pnpm --filter @warmy/web exec vitest run src/features/projects/tests src/features/agents/tests/agent-list.test.tsx src/features/datasets/tests src/features/test-plans/tests/test-plan-list.test.tsx src/features/runs/tests/run-center.test.tsx src/features/environments/tests/environment-list.test.tsx

Expected: all tests pass.

- [ ] **Step 6: Commit**

    git add apps/web/src/components/ui/resource-reference-link.tsx apps/web/src/features/projects apps/web/src/features/agents apps/web/src/features/datasets apps/web/src/features/test-plans apps/web/src/features/runs apps/web/src/features/environments
    git commit -m "feat: enrich primary asset lists"

## Task 12: Enriched quality and governance lists

**Files:**

- Modify: apps/web/src/features/scorers/scorer-list.tsx
- Modify: apps/web/src/features/scorers/api.ts
- Modify: apps/web/src/features/experiments/experiment-list.tsx
- Modify: apps/web/src/features/experiments/api.ts
- Modify: apps/web/src/features/security/security-scan.tsx
- Modify: apps/web/src/features/security/api.ts
- Modify: apps/web/src/features/reviews/review-workbench.tsx
- Modify: apps/web/src/features/reviews/api.ts
- Modify: apps/web/src/features/gates/gate-list.tsx
- Modify: apps/web/src/features/gates/api.ts
- Modify: corresponding tests

- [ ] **Step 1: Write failing summary table tests**

Assert every approved scorer, experiment, security, review and gate field, with linked resources and explicit “暂无数据” for unavailable deltas or calibration.

- [ ] **Step 2: Verify RED**

Run:

    pnpm --filter @warmy/web exec vitest run src/features/scorers/tests src/features/experiments/tests src/features/security/tests src/features/reviews/tests src/features/gates/tests

Expected: current pages omit required decision fields.

- [ ] **Step 3: Implement five summary views**

Render typed summaries through shared table primitives and ResourceReferenceLink. Compute no metrics in the browser except display formatting for durations, percentages and dates.

- [ ] **Step 4: Run focused Web checks**

Run the same Vitest command, then:

    pnpm --filter @warmy/web lint
    pnpm --filter @warmy/web typecheck

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

    git add apps/web/src/features/scorers apps/web/src/features/experiments apps/web/src/features/security apps/web/src/features/reviews apps/web/src/features/gates
    git commit -m "feat: enrich quality and governance lists"

## Task 13: Cross-module E2E and accessibility verification

**Files:**

- Create: apps/web/tests/e2e/professional-test-management.spec.ts
- Modify: apps/web/tests/e2e/list-layout.spec.ts
- Modify: frontend test fixtures only where required by the generated contract

- [ ] **Step 1: Add the E2E journey**

Cover:

1. Create or open a project with key and lead.
2. Create a dataset draft.
3. Add a full professional test case through form controls.
4. Validate and mark ready.
5. Start a single-case trial with explicit confirmation.
6. Follow Run, Agent, dataset and environment links.
7. Open all core lists and confirm decision columns.
8. Repeat layout checks at 1280 and 390.

- [ ] **Step 2: Run E2E and verify failures before final UI fixes**

Run:

    pnpm --filter @warmy/web exec playwright test tests/e2e/professional-test-management.spec.ts tests/e2e/list-layout.spec.ts --reporter=line

Expected before final fixes: any missing route, label, overflow or focus issue is reported explicitly.

- [ ] **Step 3: Apply minimal UI and fixture fixes**

Fix only failures from the new journey. Do not weaken selectors, skip assertions or hide overflow. Keep labels user-facing and resource links resolvable.

- [ ] **Step 4: Re-run E2E and build**

Run:

    pnpm --filter @warmy/web exec playwright test tests/e2e/professional-test-management.spec.ts tests/e2e/list-layout.spec.ts --reporter=line
    pnpm --filter @warmy/web build

Expected: E2E passes or only credential-dependent existing scenarios report their documented skip; production build exits 0.

- [ ] **Step 5: Commit**

    git add apps/web/tests/e2e apps/web/src
    git commit -m "test: cover professional test management journey"

## Task 14: Full verification, documentation and closure

**Files:**

- Modify: docs/Agent测试平台产品需求文档-PRD.md
- Modify: docs/Agent测试平台技术架构与开发规范.md
- Modify: docs/开发进度与变更记录.md
- Modify: docs/当前任务.md
- Modify: relevant runbook if trial execution changes operations

- [ ] **Step 1: Run backend focused and architecture gates**

Run:

    uv run ruff check apps/control-api workers plugins
    uv run mypy apps/control-api/src workers/api-runner/src plugins/canvas-agent/src
    uv run pytest apps/control-api/tests workers/api-runner/tests plugins/canvas-agent/tests -q
    uv run pytest apps/control-api/tests/architecture -q
    python scripts/check_architecture.py

Expected: all commands exit 0; default-environment PostgreSQL skips are enumerated for isolated coverage.

- [ ] **Step 2: Run isolated PostgreSQL validation**

Against a disposable PostgreSQL database:

- upgrade an empty database to head;
- upgrade a 0026 database with legacy project/case rows;
- run migration, constraint, project isolation, audit, sequence concurrency and list query-budget tests;
- inspect indexes and foreign keys;
- drop the disposable database and roles.

Expected: all targeted tests pass and no disposable database remains.

- [ ] **Step 3: Run frontend and generated-client gates**

Run:

    pnpm format:check
    pnpm lint
    pnpm typecheck
    pnpm test
    pnpm --filter @warmy/web build
    make api-check

Expected: all commands exit 0.

- [ ] **Step 4: Run repository-wide risk gates**

Run:

    make performance
    make security-audit
    make verify
    git diff --check

Expected: all mandatory gates exit 0. Any upstream-only documented dependency advisory remains governed by the existing fail-closed audit policy and is recorded without being mislabeled as fixed.

- [ ] **Step 5: Update product, architecture and progress records**

Document:

- PlatformTestCaseV1 fields and lifecycle;
- project/case keys and project_sequences;
- case_trial semantics and secret-free snapshot;
- Summary DTO and ResourceReference boundaries;
- Test Agent capabilities and risk levels;
- exact verification evidence, skips, known issues and next step.

Move TASK-20260716-001 to completed only after all required evidence exists. Reset current task to no active task while preserving external TASK-20260712-002 as pending external validation.

- [ ] **Step 6: Final verification after documentation**

Run:

    git diff --check
    make api-check
    git status --short

Expected: no whitespace or generated-contract drift; only intended task files remain before commit.

- [ ] **Step 7: Commit**

    git add docs apps/control-api apps/web workers openapi packages/generated-api-client
    git commit -m "docs: close professional test management task"

## Self-review

Spec coverage:

- Project metadata and readable keys: Tasks 2 and 7.
- Professional input, preparation, ordered steps, per-step data/expected results and postconditions: Tasks 1, 3 and 10.
- Manual form creation/editing and AI draft editing: Tasks 6 and 10.
- Import/export and failure regression: Task 3.
- Single-case execution and immutable snapshot: Tasks 4 and 5.
- All primary and quality/governance core lists: Tasks 7, 8, 11 and 12.
- Cross-resource navigation: Tasks 7, 8, 11, 12 and 13.
- Test Agent full closed loop: Task 6.
- Project isolation, immutable publication, security and N+1 budgets: Tasks 2 through 8 and 14.
- Compatibility, rollout and full verification: Tasks 2, 4, 5, 9 and 14.

Type consistency:

- PlatformTestCaseV1 is defined once in Datasets Application and re-exported through Datasets public.
- TestCaseResponse and generated TypeScript types map the same canonical names.
- Worker receives PlatformTestCaseSnapshotV1, an immutable serialized projection of PlatformTestCaseV1.
- ResourceReference is shared by Application DTOs, API responses and Test Agent result projection.
- case_trial is the persisted run_type used by backend, generated client and Web.

Placeholder scan:

- The plan contains no deferred implementation markers.
- Every task names exact files, RED command, implementation responsibility, GREEN command and commit boundary.
