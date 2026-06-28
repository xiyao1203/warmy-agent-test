# Web Test TypeScript Errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清除 Web 质量门禁当前可复现的 31 个 TypeScript 错误，并确认截图中的组件测试与 Playwright 测试文件均可被独立类型检查。

**Architecture:** 保留 `d054e99` 引入的增强版 `TestCaseEditor`，移除同文件尾部误拼接的旧版实现；表单枚举状态直接复用生成 API Client 的 `Priority`、`RiskLevel`、`TestGroup` 联合类型，避免在提交边界使用不安全断言。Playwright 使用现有独立 `playwright/tsconfig.json`，主应用继续排除旧 Playwright 目录，两个测试目录分别执行类型检查和测试收集。

**Tech Stack:** Next.js 16、React 19、TypeScript 6、Vitest、Testing Library、Playwright、pnpm 11。

---

### Task 1: 固化增强测试用例编辑器的提交契约

**Files:**
- Modify: `apps/web/src/features/datasets/tests/dataset-list.test.tsx`
- Test: `apps/web/src/features/datasets/tests/dataset-list.test.tsx`

- [x] **Step 1: 写入失败的回归测试**

在测试文件中导入 `TestCaseEditor`，渲染后依次填写基本信息、切换各分区、填写 JSON，并断言 `onSubmit` 收到 API 契约允许的枚举字段：

```tsx
it("submits enhanced test case fields with API enum values", async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  render(
    <TestCaseEditor
      onSubmit={onSubmit}
      triggerLabel="添加测试用例"
    />,
  );

  fireEvent.click(screen.getByRole("button", { name: "添加测试用例" }));
  fireEvent.change(screen.getByLabelText("用例名称"), {
    target: { value: "权限回归" },
  });
  fireEvent.change(screen.getByLabelText("优先级"), {
    target: { value: "P1" },
  });
  fireEvent.change(screen.getByLabelText("风险等级"), {
    target: { value: "high" },
  });
  fireEvent.change(screen.getByLabelText("测试分组"), {
    target: { value: "validation" },
  });
  fireEvent.click(screen.getByRole("button", { name: "保存用例" }));

  await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
  expect(onSubmit).toHaveBeenCalledWith(
    expect.objectContaining({
      name: "权限回归",
      priority: "P1",
      risk_level: "high",
      test_group: "validation",
    }),
  );
});
```

- [x] **Step 2: 运行测试并确认 RED**

Run: `pnpm --filter @warmy/web test -- src/features/datasets/tests/dataset-list.test.tsx`

Expected: FAIL；当前重复组件使转换失败或类型检查阻塞，证明测试覆盖实际损坏文件。

### Task 2: 删除重复实现并收紧枚举类型

**Files:**
- Modify: `apps/web/src/features/datasets/test-case-editor.tsx`
- Test: `apps/web/src/features/datasets/tests/dataset-list.test.tsx`

- [x] **Step 1: 复用生成客户端的枚举类型**

扩展类型导入，并让可选表单状态保留空字符串作为“未设置”值：

```tsx
import type {
  CreateTestCaseRequest,
  Priority,
  RiskLevel,
  TestCaseResponse,
  TestGroup,
} from "@warmy/generated-api-client";

const [priority, setPriority] = useState<Priority | "">(
  caseItem?.priority ?? "",
);
const [riskLevel, setRiskLevel] = useState<RiskLevel | "">(
  caseItem?.risk_level ?? "",
);
const [testGroup, setTestGroup] = useState<TestGroup | "">(
  caseItem?.test_group ?? "",
);
```

三个 `<select>` 的 `onChange` 分别转换为对应的 `Priority | ""`、`RiskLevel | ""`、`TestGroup | ""`；`difficulty` 保持生成契约可接受的现有类型。

- [x] **Step 2: 删除误拼接的旧版组件**

删除第一个增强版 `JsonField` 结束后的第二个 `"use client"`、重复 imports、旧版 `TestCaseEditor` 和旧版 `JsonField`，保证文件只导出一个组件实现。

- [x] **Step 3: 运行回归测试并确认 GREEN**

Run: `pnpm --filter @warmy/web test -- src/features/datasets/tests/dataset-list.test.tsx`

Expected: PASS。

- [x] **Step 4: 运行项目与 Playwright 类型检查**

Run: `pnpm --filter @warmy/web typecheck`

Run: `pnpm --filter @warmy/web exec tsc --noEmit -p playwright/tsconfig.json`

Expected: 两个命令均退出码 0，无 TypeScript diagnostics。

### Task 3: 全量前端质量门禁与记录

**Files:**
- Modify: `apps/web/playwright/tsconfig.json`
- Modify: `apps/web/vitest.config.ts`
- Modify: `apps/web/src/features/runs/tests/run-center.test.tsx`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Modify: `docs/superpowers/plans/2026-06-28-web-test-typescript-errors.md`

- [x] **Step 1: 验证截图涉及的 Playwright 测试可被收集**

先将 `node` 与 `@playwright/test` 加入 `playwright/tsconfig.json` 的 `types`，并在 Vitest `exclude` 中加入 `tests/e2e/**`；运行详情的两个“执行摘要”是有意存在的主区与侧栏标题，断言改用 `getAllByText` 并校验数量为 2。

Run: `pnpm --filter @warmy/web exec playwright test --list`

Expected: Playwright 成功列出 `apps/web/tests/e2e` 测试，无模块或 fixture 隐式 `any` 错误。

- [x] **Step 2: 运行全量 Web 验证**

Run: `pnpm --filter @warmy/web lint`

Run: `pnpm --filter @warmy/web test`

Run: `pnpm --filter @warmy/web build`

Expected: Lint、全部 Vitest 和 Next.js Build 通过。

- [x] **Step 3: 检查变更边界**

Run: `git diff --check && git status --short && git diff --stat`

Expected: 无空白错误；仅包含本任务代码、测试、计划与进度记录。

- [x] **Step 4: 更新任务与进度记录**

将 `TASK-20260628-012` 标记为已完成，写入根因、实际变更、每条验证命令及结果；若真实浏览器 E2E 因后端或测试账号缺失未运行，明确记录“仅完成测试收集，未执行真实旅程”。

## Plan Review

- Spec coverage：覆盖截图文件、项目 TypeScript、独立 Playwright TypeScript、测试收集、Lint、组件测试和 Build。
- Placeholder scan：无 TBD/TODO/模糊实现步骤。
- Type consistency：枚举类型均来自生成 API Client，与 `CreateTestCaseRequest` 字段一致。
