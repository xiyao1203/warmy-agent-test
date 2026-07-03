# Agent Chat Balanced UI Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine the Test Agent chat into a quiet ChatGPT-style reading surface with a compact Codex-style execution timeline and fully functional desktop/mobile interactions.

**Architecture:** Keep session and generation orchestration in `TestAgentChat`, move display grouping into a pure timeline projection, and keep presentation in focused components. Reuse repository tokens, Lucide icons, reducer state, and existing API contracts; do not change backend behavior.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, Vitest, Testing Library, Lucide React.

---

### Task 1: Project tool events into compact timeline groups

**Files:**
- Create: `apps/web/src/features/test-agent/timeline-projection.ts`
- Create: `apps/web/src/features/test-agent/tests/timeline-projection.test.ts`
- Modify: `apps/web/src/features/test-agent/conversation-timeline.tsx`

- [ ] **Step 1: Write the failing projection tests**

Cover a delegated/progress/completed sequence with one `task_id`, a standalone confirmation, and a cancelled generation. Assert the three tool events become one item with `status: "completed"`, while confirmation and cancellation preserve their own positions.

```ts
const projected = projectTimeline(items);
expect(projected.filter((item) => item.kind === "tool")).toHaveLength(1);
expect(projected).toEqual(expect.arrayContaining([
  expect.objectContaining({ kind: "tool", status: "completed" }),
]));
```

- [ ] **Step 2: Run the projection test and verify RED**

Run: `pnpm --dir apps/web exec vitest run src/features/test-agent/tests/timeline-projection.test.ts`

Expected: FAIL because `timeline-projection` does not exist.

- [ ] **Step 3: Implement the pure projection**

Export a discriminated `ConversationItem` union and `projectTimeline(items)`. Group only `agent.delegated`, `agent.progress`, `agent.completed`, and `agent.failed` entries sharing a non-empty `task_id`; preserve the first position and use the latest state. Pass messages, reasoning, confirmations, generation cancellation, and unmatched events through unchanged.

```ts
export type ToolTimelineItem = {
  kind: "tool";
  id: string;
  taskId: string;
  label: string;
  summary: string;
  status: "queued" | "running" | "completed" | "failed";
  details: Record<string, unknown>;
};
```

- [ ] **Step 4: Render grouped items with expandable details**

Update `ConversationTimeline` to consume `projectTimeline(items)`. Render one compact process row per tool with a native `<button aria-expanded>` and a detail region containing safe summaries/outputs. Keep assistant messages borderless and user messages in a restrained bubble.

- [ ] **Step 5: Run tests and commit**

Run: `pnpm --dir apps/web exec vitest run src/features/test-agent/tests/timeline-projection.test.ts src/features/test-agent/tests/conversation-timeline.test.tsx`

Expected: PASS.

Commit: `feat: compact agent execution timeline`

### Task 2: Refine confirmation and process-state interaction

**Files:**
- Modify: `apps/web/src/features/test-agent/confirmation-card.tsx`
- Modify: `apps/web/src/features/test-agent/tests/conversation-timeline.test.tsx`
- Create: `apps/web/src/features/test-agent/tests/confirmation-card.test.tsx`

- [ ] **Step 1: Write failing confirmation interaction tests**

Render a confirmation with arguments. Assert parameters are hidden initially, the “查看参数” button toggles `aria-expanded`, rejecting and approving expose distinct labels, and busy state disables only the card actions.

```tsx
expect(screen.queryByText("project_id")).not.toBeInTheDocument();
fireEvent.click(screen.getByRole("button", { name: "查看参数" }));
expect(screen.getByText("project_id")).toBeVisible();
```

- [ ] **Step 2: Run the confirmation test and verify RED**

Run: `pnpm --dir apps/web exec vitest run src/features/test-agent/tests/confirmation-card.test.tsx`

Expected: FAIL because arguments are always visible and no disclosure exists.

- [ ] **Step 3: Implement compact confirmation UI**

Add local `expanded` and `decision` state. Use an inline timeline-compatible container, a concise action/risk header, a native disclosure button, and explicit `正在执行` / `正在拒绝` labels. Retain existing API parameters and `onDecided` behavior.

- [ ] **Step 4: Verify interaction and commit**

Run: `pnpm --dir apps/web exec vitest run src/features/test-agent/tests/confirmation-card.test.tsx src/features/test-agent/tests/conversation-timeline.test.tsx`

Expected: PASS.

Commit: `feat: refine agent confirmation interaction`

### Task 3: Refine chat shell, header, composer, and responsive drawers

**Files:**
- Modify: `apps/web/src/features/test-agent/chat-screen.tsx`
- Modify: `apps/web/src/features/test-agent/session-list.tsx`
- Modify: `apps/web/src/features/test-agent/context-panel.tsx`
- Modify: `apps/web/src/features/test-agent/tests/session-history.test.tsx`
- Create: `apps/web/src/features/test-agent/tests/chat-shell.test.tsx`

- [ ] **Step 1: Write failing shell behavior tests**

Mock the chat APIs and render `TestAgentChat`. Assert the composer placeholder contains only the task prompt, keyboard help is separate, context and history toggles have accessible labels, and mobile drawer controls exist without duplicating desktop content in the accessibility tree.

```tsx
expect(screen.getByPlaceholderText("向超级测试 Agent 描述目标…")).toBeVisible();
expect(screen.getByText("Enter 发送 · Shift+Enter 换行")).toBeVisible();
expect(screen.getByRole("button", { name: "打开会话历史" })).toBeVisible();
expect(screen.getByRole("button", { name: "打开上下文" })).toBeVisible();
```

- [ ] **Step 2: Run the shell test and verify RED**

Run: `pnpm --dir apps/web exec vitest run src/features/test-agent/tests/chat-shell.test.tsx`

Expected: FAIL on missing labels and current placeholder text.

- [ ] **Step 3: Implement the refined layout**

Use a 48px header, 260px default history rail, 288px context rail, and a 768px shared reading/composer width. Add explicit history/context buttons. Below 1100px render context as an accessible overlay panel; below 760px render history as an overlay panel and remove persistent main-column margins. Keep all controls connected to existing state and callbacks.

- [ ] **Step 4: Implement the floating composer**

Wrap the textarea and send/stop control in one rounded surface. Keep the button slot stable, auto-grow to 8 lines, move shortcut text outside the placeholder, and retain Enter/Shift+Enter semantics. Preserve connection and error status immediately above the composer.

- [ ] **Step 5: Refine side panels**

Make session rows 36–40px high with restrained active styling and touch-accessible delete/menu behavior. Reduce context-panel headings and empty-state weight. Do not change API calls or artifact links.

- [ ] **Step 6: Verify and commit**

Run: `pnpm --dir apps/web exec vitest run src/features/test-agent/tests/chat-shell.test.tsx src/features/test-agent/tests/session-history.test.tsx`

Expected: PASS.

Commit: `feat: refine responsive agent chat shell`

### Task 4: Polish motion, focus, Markdown overflow, and reduced-motion behavior

**Files:**
- Modify: `apps/web/src/app/globals.css`
- Modify: `apps/web/src/components/uiverse/chat/markdown-content.tsx`
- Modify: `apps/web/src/features/test-agent/conversation-timeline.tsx`
- Modify: `apps/web/src/features/test-agent/tests/conversation-timeline.test.tsx`

- [ ] **Step 1: Add failing semantic assertions**

Assert disclosure controls expose `aria-expanded`, timeline content has no replay-only stagger classes, and assistant Markdown is wrapped in a stable overflow container.

- [ ] **Step 2: Run the component test and verify RED**

Run: `pnpm --dir apps/web exec vitest run src/features/test-agent/tests/conversation-timeline.test.tsx`

Expected: FAIL on the missing disclosure/overflow semantics.

- [ ] **Step 3: Implement global and component polish**

Include `textarea` in focus-visible rules, remove global `body *` transitions and nth-child timeline delays, scope 160–220ms transitions to interactive components, constrain Markdown tables/code blocks, and add `@media (prefers-reduced-motion: reduce)` rules that disable smooth scrolling and nonessential transforms.

- [ ] **Step 4: Verify and commit**

Run: `pnpm --dir apps/web exec prettier --check src/app/globals.css src/components/uiverse/chat/markdown-content.tsx src/features/test-agent/conversation-timeline.tsx`

Run: `pnpm --dir apps/web exec vitest run src/features/test-agent/tests`

Expected: formatting and tests pass.

Commit: `style: polish agent chat motion and typography`

### Task 5: Full verification, visual QA, and task records

**Files:**
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Run frontend quality gates**

Run:

```bash
pnpm --dir apps/web exec prettier --check src/app/globals.css src/features/test-agent
pnpm --dir apps/web exec eslint src/features/test-agent src/app/globals.css
pnpm --dir apps/web typecheck
pnpm --dir apps/web exec vitest run src/features/test-agent/tests
pnpm --dir apps/web build
```

Expected: all changed-scope checks pass. Record unrelated full-suite failures separately without weakening rules.

- [ ] **Step 2: Perform browser visual QA**

Using the in-app browser and authenticated local workspace, verify empty, historical, streaming, tool, confirmation, cancelled, reconnecting, and error states at 1440px, 1024px, and 390px. Confirm no horizontal page scroll, no clipped composer, accessible drawer controls, and stable send/stop placement.

- [ ] **Step 3: Update repository records**

Record actual files, commands, results, visual QA evidence, remaining Temporal/model E2E risk, and any browser limitation. Keep the task `待验证` unless every acceptance item has evidence.

- [ ] **Step 4: Commit the verification record**

Commit: `docs: record agent chat ui verification`
