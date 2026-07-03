# Agent Chat Codex Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a recoverable, cancellable Test Agent conversation with cursor-safe SSE and a ChatGPT-style reading surface containing a Codex-style inline execution timeline.

**Architecture:** PostgreSQL remains the source of truth for chat messages, semantic events, confirmations, and a new per-turn `ChatGeneration` lifecycle. The Control API exposes snapshot + cursor recovery, an explicit SSE ready handshake, and an idempotent cancellation endpoint backed by Temporal workflow cancellation. The Web client renders one ordered timeline from the server snapshot, merging only events newer than its cursor.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL/SQLite tests, Temporal Python SDK, Next.js, React, TypeScript, Vitest, Testing Library.

---

## File map

- Create `apps/control-api/migrations/versions/0015_test_agent_chat_generations.py`: additive generation table and event correlation field.
- Modify `apps/control-api/src/agenttest/modules/test_agent/domain/entities.py`: generation state machine.
- Modify `apps/control-api/src/agenttest/modules/test_agent/application/ports.py`: generation persistence and cancellation ports.
- Modify `apps/control-api/src/agenttest/modules/test_agent/infrastructure/models.py`: generation ORM and event generation ID.
- Modify `apps/control-api/src/agenttest/modules/test_agent/infrastructure/persistence/repositories.py`: project-scoped generation CRUD and recoverable timeline reads.
- Create `apps/control-api/src/agenttest/modules/test_agent/application/generations.py`: generation coordinator and terminal-state convergence.
- Modify `apps/control-api/src/agenttest/modules/test_agent/application/conversation.py`: pass `StreamContext`; plan/tools precede final response.
- Modify `apps/control-api/src/agenttest/modules/test_agent/api/router.py`: snapshot timeline, ready handshake, generation ID, cancellation API.
- Modify `apps/control-api/src/agenttest/bootstrap/app.py`: wire generation coordinator and model cancellation port.
- Modify `apps/control-api/src/agenttest/modules/model_configs/application/ports.py` and `infrastructure/temporal_invoker.py`: stable workflow ID and cancellation result semantics.
- Modify `workers/model-runner/src/agenttest_model_runner/workflow.py` and `activities.py`: preserve partial content on cancellation.
- Modify `apps/web/src/features/test-agent/api.ts`: timeline/generation contracts, ready-aware SSE, cancel API.
- Modify `apps/web/src/features/test-agent/chat-reducer.ts`: snapshot/cursor/connection/generation state model.
- Split `apps/web/src/features/test-agent/chat-screen.tsx` by creating `conversation-timeline.tsx` and `chat-composer.tsx`.
- Modify `apps/web/src/components/uiverse/chat/reasoning-block.tsx` and `tool-call-card.tsx`: low-noise accessible inline steps.
- Extend backend, worker, and Web tests listed in the tasks below.

### Task 1: Persist the generation lifecycle

**Files:**
- Create: `apps/control-api/migrations/versions/0015_test_agent_chat_generations.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/infrastructure/models.py`
- Test: `apps/control-api/tests/unit/test_agent/test_chat_generation.py`
- Test: `apps/control-api/tests/integration/test_migrations.py`
- Test: `apps/control-api/tests/integration/test_database_constraints.py`

- [ ] **Step 1: Write failing generation state-machine tests**

```python
def test_generation_cancellation_is_idempotent() -> None:
    generation = ChatGeneration.create(project_id=PROJECT_ID, session_id=SESSION_ID,
                                       generation_id=GENERATION_ID)
    generation.start("model-streaming-fixed")
    generation.request_cancel()
    generation.cancel("partial")
    generation.cancel("partial")
    assert generation.status is GenerationStatus.CANCELLED
    assert generation.partial_content == "partial"

def test_completed_generation_cannot_be_cancelled() -> None:
    generation = ChatGeneration.create(project_id=PROJECT_ID, session_id=SESSION_ID,
                                       generation_id=GENERATION_ID)
    generation.start("model-streaming-fixed")
    generation.complete("done")
    with pytest.raises(ValueError, match="terminal"):
        generation.request_cancel()
```

- [ ] **Step 2: Run the unit test and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_chat_generation.py -q`
Expected: FAIL because `ChatGeneration` and `GenerationStatus` do not exist.

- [ ] **Step 3: Implement the minimal domain entity and status transitions**

```python
class GenerationStatus(StrEnum):
    PENDING = "pending"; RUNNING = "running"; CANCELLING = "cancelling"
    COMPLETED = "completed"; CANCELLED = "cancelled"; FAILED = "failed"

@dataclass(slots=True)
class ChatGeneration:
    generation_id: UUID
    project_id: UUID
    session_id: UUID
    workflow_id: str | None
    status: GenerationStatus
    partial_content: str
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None
```

- [ ] **Step 4: Add migration and ORM model**

Create `test_agent_chat_generations` with composite project/session foreign key, unique `(project_id, id)`, index `(project_id, session_id, status)`, workflow ID, partial content, and timestamps. Add nullable `generation_id` to `test_agent_events` with a project-scoped composite foreign key and an index. Keep the new field nullable for old events.

- [ ] **Step 5: Verify migration and domain tests GREEN**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_chat_generation.py apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/integration/test_database_constraints.py -q`
Expected: PASS, or PostgreSQL-only tests SKIP with the existing documented environment reason.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/migrations/versions/0015_test_agent_chat_generations.py apps/control-api/src/agenttest/modules/test_agent/domain/entities.py apps/control-api/src/agenttest/modules/test_agent/infrastructure/models.py apps/control-api/tests/unit/test_agent/test_chat_generation.py apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/integration/test_database_constraints.py
git commit -m "feat: persist test agent chat generations"
```

### Task 2: Add project-scoped generation and timeline repositories

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/infrastructure/persistence/repositories.py`
- Test: `apps/control-api/tests/unit/test_agent/test_session_repository.py`

- [ ] **Step 1: Write failing repository tests**

```python
async def test_session_snapshot_restores_semantic_events_and_pending_generation(repository):
    snapshot = await repository.get_snapshot(PROJECT_ID, SESSION_ID)
    assert [item.kind for item in snapshot.timeline] == ["message", "reasoning", "tool"]
    assert snapshot.event_cursor == 7
    assert snapshot.active_generation.generation_id == GENERATION_ID

async def test_generation_lookup_is_project_isolated(repository):
    assert await repository.get_generation(OTHER_PROJECT, GENERATION_ID) is None
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_session_repository.py -q`
Expected: FAIL because snapshot and generation repository methods are missing.

- [ ] **Step 3: Define focused ports and snapshot DTOs**

```python
class ChatGenerationRepository(Protocol):
    async def add(self, generation: ChatGeneration) -> None: ...
    async def get(self, project_id: ProjectId, generation_id: UUID) -> ChatGeneration | None: ...
    async def get_active(self, project_id: ProjectId, session_id: ChatSessionId) -> ChatGeneration | None: ...
    async def save(self, generation: ChatGeneration) -> None: ...

@dataclass(frozen=True, slots=True)
class ConversationSnapshot:
    session: ChatSession
    semantic_events: list[AgentEvent]
    event_cursor: int
    active_generation: ChatGeneration | None
```

- [ ] **Step 4: Implement SQLAlchemy persistence and semantic-event filtering**

Filter replayable event types through one named constant; exclude raw `message.delta` and `agent.reasoning_delta`. Every query must include `project_id` and session/generation identity.

- [ ] **Step 5: Run repository tests GREEN**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_session_repository.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/src/agenttest/modules/test_agent/application/ports.py apps/control-api/src/agenttest/modules/test_agent/infrastructure/persistence/repositories.py apps/control-api/tests/unit/test_agent/test_session_repository.py
git commit -m "feat: restore agent chat timeline snapshots"
```

### Task 3: Make Temporal streaming externally cancellable

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/model_configs/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/model_configs/infrastructure/temporal_invoker.py`
- Modify: `workers/model-runner/src/agenttest_model_runner/workflow.py`
- Modify: `workers/model-runner/src/agenttest_model_runner/activities.py`
- Test: `apps/control-api/tests/unit/model_configs/test_temporal_invoker.py`
- Test: `workers/model-runner/tests/test_workflow.py`

- [ ] **Step 1: Write failing stable-workflow and cancellation tests**

```python
async def test_stream_uses_requested_workflow_id(invoker, temporal_client):
    context = StreamContext(workflow_id="chat-generation-123")
    await invoker.stream(CONFIG, MESSAGES, callback=CALLBACK, stream_ctx=context)
    assert temporal_client.started_id == "chat-generation-123"

async def test_cancel_returns_partial_content():
    result = await run_cancelled_stream(chunks=["partial ", "answer"])
    assert result == {"content": "partial answer", "cancelled": True}
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/model_configs/test_temporal_invoker.py workers/model-runner/tests/test_workflow.py -q`
Expected: FAIL because StreamContext cannot supply a stable ID and cancellation discards partial content.

- [ ] **Step 3: Implement stable StreamContext and cancellation result**

```python
@dataclass
class StreamContext:
    workflow_id: str | None = None
    cancelled: bool = False
```

Use an existing `workflow_id` when supplied; generate one only when absent. Do not erase it in `finally`. Return the Worker `cancelled` flag through `InvocationResult`.

- [ ] **Step 4: Preserve accumulated content in the Worker activity/workflow**

The activity must catch `asyncio.CancelledError`, return accumulated sanitized content, and re-raise only when no safe result can be produced. The workflow returns that payload unchanged.

- [ ] **Step 5: Run cancellation tests GREEN**

Run: `uv run pytest apps/control-api/tests/unit/model_configs/test_temporal_invoker.py workers/model-runner/tests -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/src/agenttest/modules/model_configs workers/model-runner apps/control-api/tests/unit/model_configs/test_temporal_invoker.py
git commit -m "feat: cancel model streams by generation"
```

### Task 4: Coordinate generation start, completion, failure, and cancellation

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_agent/application/generations.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/conversation.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/orchestrator.py`
- Test: `apps/control-api/tests/unit/test_agent/test_generation_coordinator.py`
- Test: `apps/control-api/tests/unit/test_agent/test_conversation.py`

- [ ] **Step 1: Write failing coordinator tests**

```python
async def test_cancel_converges_on_one_terminal_state(coordinator):
    await coordinator.cancel(PROJECT_ID, SESSION_ID, GENERATION_ID)
    generation = await coordinator.get(PROJECT_ID, GENERATION_ID)
    assert generation.status in {GenerationStatus.CANCELLING, GenerationStatus.CANCELLED}
    invoker.cancel_workflow.assert_awaited_once_with(generation.workflow_id)

async def test_tool_events_precede_final_message(conversation):
    await conversation.respond(...)
    assert event_types.index("agent.delegated") < event_types.index("message.completed")
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_generation_coordinator.py apps/control-api/tests/unit/test_agent/test_conversation.py -q`
Expected: FAIL because the coordinator does not exist and current message completion precedes delegation.

- [ ] **Step 3: Implement `GenerationCoordinator`**

```python
class GenerationCoordinator:
    async def begin(self, project_id, session_id, generation_id) -> ChatGeneration: ...
    async def attach_workflow(self, generation, workflow_id) -> None: ...
    async def complete(self, generation, content) -> None: ...
    async def fail(self, generation, detail) -> None: ...
    async def cancel(self, project_id, session_id, generation_id) -> ChatGeneration: ...
```

All methods append correlated semantic events and make terminal transitions idempotent.

- [ ] **Step 4: Reorder conversation execution**

Generate a safe action summary, delegate/execute or wait for confirmation, then produce the final user-facing response from tool results. Pass the stable `StreamContext` into every streamed model call. Never expose raw private reasoning.

For write capabilities, keep the generation in `running` with a `waiting_confirmation` phase. Approval resumes the same `generation_id`, executes the capability, and generates the final answer once all tasks are terminal. Rejection emits a cancelled tool result and resumes final-answer generation with the rejection context; it must not leave the generation permanently active.

- [ ] **Step 5: Run coordinator/conversation tests GREEN**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_generation_coordinator.py apps/control-api/tests/unit/test_agent/test_conversation.py apps/control-api/tests/unit/test_agent/test_orchestrator.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/src/agenttest/modules/test_agent/application apps/control-api/tests/unit/test_agent
git commit -m "feat: coordinate agent chat generations"
```

### Task 5: Expose recoverable session, ready SSE, and cancel APIs

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/test_agent/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Test: `apps/control-api/tests/contract/test_super_agent_chat_api.py`

- [ ] **Step 1: Write failing contract tests**

```python
def test_session_restores_timeline_cursor_and_active_generation(client):
    body = client.get(session_url).json()
    assert body["event_cursor"] >= 1
    assert body["timeline"][0]["kind"] == "message"
    assert body["active_generation"]["generation_id"] == generation_id

def test_sse_starts_with_ready_and_replays_after_cursor(client):
    stream = client.get(events_url + "?after=1")
    assert "event: stream.ready" in stream.text
    assert '"cursor":1' in stream.text

def test_cancel_is_idempotent(client):
    first = client.post(cancel_url, headers=csrf)
    second = client.post(cancel_url, headers=csrf)
    assert first.status_code == second.status_code == 200

def test_approval_resumes_the_same_generation(client):
    approved = client.post(confirmation_url, headers=csrf, json={"approved": True})
    assert approved.json()["generation_id"] == generation_id
    restored = client.get(session_url).json()
    assert restored["active_generation"] is None
    assert restored["timeline"][-1]["kind"] == "assistant_message"
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest apps/control-api/tests/contract/test_super_agent_chat_api.py -q`
Expected: FAIL because snapshot, ready, generation ID, and cancel contract are absent.

- [ ] **Step 3: Implement request/response contracts**

`ChatRequest` gains `generation_id: UUID`. Session responses gain `timeline`, `event_cursor`, and `active_generation`. SSE takes `after` query with `Last-Event-ID` fallback, emits `stream.ready` first, then events strictly greater than the selected cursor.

- [ ] **Step 4: Implement cancellation endpoint and bootstrap wiring**

Add `POST /sessions/{session_id}/generations/{generation_id}/cancel`, requiring the existing project writer and CSRF guards. Return the current generation status for repeated terminal calls.

- [ ] **Step 5: Run contract and security tests GREEN**

Run: `uv run pytest apps/control-api/tests/contract/test_super_agent_chat_api.py apps/control-api/tests/security/test_session_security.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/src/agenttest/modules/test_agent/api/router.py apps/control-api/src/agenttest/bootstrap/app.py apps/control-api/tests/contract/test_super_agent_chat_api.py apps/control-api/tests/security/test_session_security.py
git commit -m "feat: expose recoverable agent chat streams"
```

### Task 6: Build the Web snapshot/cursor state machine

**Files:**
- Modify: `apps/web/src/features/test-agent/api.ts`
- Modify: `apps/web/src/features/test-agent/chat-reducer.ts`
- Create: `apps/web/src/features/test-agent/tests/chat-reducer.test.ts`
- Modify: `apps/web/src/features/test-agent/tests/session-history.test.tsx`

- [ ] **Step 1: Write failing reducer and handshake tests**

```typescript
it("merges only events newer than the snapshot cursor", () => {
  const loaded = chatReducer(initialChatState(), applySnapshot(snapshotAt7));
  const duplicate = chatReducer(loaded, addEvent(event7));
  const next = chatReducer(duplicate, addEvent(event8));
  expect(next.timeline).toHaveLength(snapshotAt7.timeline.length + 1);
  expect(next.eventCursor).toBe(8);
});

it("does not send until stream.ready", async () => {
  render(<TestAgentChat projectId="project-1" />);
  await user.type(screen.getByLabelText("对话输入"), "hello");
  await user.click(screen.getByLabelText("发送"));
  expect(sendChatMessage).not.toHaveBeenCalled();
  emit({ type: "stream.ready", payload: { cursor: 0 } });
  expect(sendChatMessage).toHaveBeenCalledOnce();
});
```

- [ ] **Step 2: Run and verify RED**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent/tests/chat-reducer.test.ts src/features/test-agent/tests/session-history.test.tsx`
Expected: FAIL because timeline/cursor/ready states are missing.

- [ ] **Step 3: Add typed contracts and reducer state**

```typescript
type ConnectionState = "connecting" | "ready" | "reconnecting" | "offline";
type GenerationStatus = "pending" | "running" | "cancelling" | "completed" | "cancelled" | "failed";
type TimelineItem = MessageTimelineItem | ReasoningTimelineItem | ToolTimelineItem | StatusTimelineItem;
```

`subscribeToSession` accepts an explicit cursor, handles `stream.ready`, catches invalid event JSON without tearing down the page, and returns a close function. Generate `generation_id` with `crypto.randomUUID()` before sending.

- [ ] **Step 4: Implement snapshot merge and ready gate**

Remove the 800ms completion timer. Completion and cancellation must come only from terminal server events. Session switching resets local drafts and rejects callbacks from the previous session.

- [ ] **Step 5: Run Web state tests GREEN**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent/tests/chat-reducer.test.ts src/features/test-agent/tests/session-history.test.tsx`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/features/test-agent/api.ts apps/web/src/features/test-agent/chat-reducer.ts apps/web/src/features/test-agent/tests
git commit -m "feat: recover agent chat stream state"
```

### Task 7: Implement the ChatGPT/Codex conversation surface

**Files:**
- Create: `apps/web/src/features/test-agent/conversation-timeline.tsx`
- Create: `apps/web/src/features/test-agent/chat-composer.tsx`
- Modify: `apps/web/src/features/test-agent/chat-screen.tsx`
- Modify: `apps/web/src/components/uiverse/chat/reasoning-block.tsx`
- Modify: `apps/web/src/components/uiverse/chat/tool-call-card.tsx`
- Modify: `apps/web/src/app/globals.css`
- Create: `apps/web/src/features/test-agent/tests/conversation-timeline.test.tsx`

- [ ] **Step 1: Write failing timeline accessibility and ordering tests**

```typescript
it("renders reasoning, tool and answer in server order", () => {
  render(<ConversationTimeline items={orderedItems} />);
  expect(screen.getAllByTestId("timeline-item").map(node => node.dataset.kind))
    .toEqual(["user-message", "reasoning", "tool", "assistant-message"]);
});

it("marks cancelled partial answers without calling them complete", () => {
  render(<ConversationTimeline items={cancelledItems} />);
  expect(screen.getByText("已停止")).toBeVisible();
  expect(screen.queryByLabelText("完成")).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run and verify RED**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent/tests/conversation-timeline.test.tsx`
Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement the inline timeline**

Render server-ordered items directly. Reasoning displays only safe summaries and defaults collapsed after completion. Tool steps expose `aria-expanded`, visible status text, and expandable input/result/error summaries. Pending confirmations remain inline beside their originating tool.

- [ ] **Step 4: Implement composer generation controls**

Replace local Abort-only stopping with `cancelGeneration`. While cancellation is pending, show `取消中…` and disable duplicate cancellation. Remove the message-count progress bar. Show a compact connection label only in reconnecting/offline states.

- [ ] **Step 5: Refactor `chat-screen.tsx` without changing unrelated workspaces**

Keep session sidebar, target-chat switch, context panel, shortcuts, edit/regenerate, auto-scroll, and artifact behavior. Move only timeline rendering and composer responsibilities to the new files.

- [ ] **Step 6: Run component tests, typecheck, and accessibility checks GREEN**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent/tests && pnpm --filter @warmy/web typecheck`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/features/test-agent apps/web/src/components/uiverse/chat apps/web/src/app/globals.css
git commit -m "feat: add codex style agent chat timeline"
```

### Task 8: Regenerate contracts, run full verification, and close records

**Files:**
- Modify: `docs/api/openapi.json`
- Modify: `packages/generated-api-client/`
- Modify: `docs/开发进度与变更记录.md`
- Modify: `docs/当前任务.md`

- [ ] **Step 1: Add end-to-end regression coverage for recovery/cancel flow**

Extend the existing browser E2E with: create session, wait for ready, send, observe ordered tool state, refresh while confirmation is pending, approve, start another response, cancel, refresh, and verify cancelled partial content.

- [ ] **Step 2: Regenerate and check API contracts**

Run: `make api-generate && make api-check`
Expected: generated OpenAPI/client matches the server with no drift.

- [ ] **Step 3: Run targeted backend and Worker verification**

Run: `uv run pytest apps/control-api/tests/unit/test_agent apps/control-api/tests/contract/test_super_agent_chat_api.py workers/model-runner/tests -q`
Expected: PASS.

- [ ] **Step 4: Run full quality gates**

Run: `make verify`
Expected: PASS. Any pre-existing failure must be reproduced on the base commit and recorded rather than hidden.

- [ ] **Step 5: Perform browser visual QA**

At desktop and narrow viewport, capture empty, streaming, tool-running, waiting-confirmation, failed, cancelled, and restored states. Compare against the approved A direction; verify spacing, focus, scroll pinning, no clipped controls, and readable status hierarchy.

- [ ] **Step 6: Update task records with exact evidence**

Move TASK-20260703-001 to completed only if all required gates pass. Otherwise use `待验证` and name each missing external verification and its risk. Preserve the user's existing `apps/web/next-env.d.ts` modification.

- [ ] **Step 7: Commit final generated artifacts and records**

```bash
git add docs/api/openapi.json packages/generated-api-client docs/当前任务.md docs/开发进度与变更记录.md
git commit -m "docs: record agent chat verification"
```
