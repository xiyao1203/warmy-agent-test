# 全站列表 UI 统一 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让所有业务列表在常见视口无横向滚动、长文本可查看全文、操作按钮紧凑一致，并把项目编辑迁移到弹窗。

**Architecture:** 扩展现有共享 Table/Tooltip 能力，新增无业务依赖的 TruncatedText 和 TableActionButton；业务 Feature 只声明列宽、文本和动作语义。后端 API、权限和数据契约不变。

**Tech Stack:** React 19、TypeScript Strict、Tailwind CSS、Radix UI、Lucide React、Vitest、Testing Library、Playwright。

---

### Task 1: 共享列表组件

**Files:**
- Modify: `apps/web/src/components/ui/table.tsx`
- Modify: `apps/web/src/components/ui/table-actions.tsx`
- Modify: `apps/web/src/components/uiverse/feedback/tooltip.tsx`
- Create: `apps/web/src/components/ui/truncated-text.tsx`
- Test: `apps/web/src/components/ui/table.test.tsx`
- Create: `apps/web/src/components/ui/table-actions.test.tsx`
- Create: `apps/web/src/components/ui/truncated-text.test.tsx`

- [x] 写失败测试，断言表格不再创建横向滚动容器、长文本保留全文提示、操作按钮仅显示图标且尺寸一致。
- [x] 运行三个组件测试，确认因能力缺失而失败。
- [x] 实现固定布局容器、可聚焦截断文本、Tooltip focus 状态和图标操作按钮。
- [x] 重跑组件测试并通过。

### Task 2: 项目列表闭环

**Files:**
- Modify: `apps/web/src/features/projects/project-list-screen.tsx`
- Modify: `apps/web/src/features/projects/tests/project-list-screen.test.tsx`

- [x] 将项目测试改为期望 Dialog 编辑、长名称全文提示和三个纯图标动作。
- [x] 运行项目测试，确认旧行内编辑按预期失败。
- [x] 使用共享组件重构项目列和操作列，新增受控编辑 Dialog。
- [x] 重跑项目测试并通过。

### Task 3: 核心资产和执行列表

**Files:**
- Modify: `apps/web/src/features/agents/agent-list.tsx`
- Modify: `apps/web/src/features/datasets/dataset-list.tsx`
- Modify: `apps/web/src/features/test-plans/test-plan-list.tsx`
- Modify: `apps/web/src/features/runs/run-center.tsx`
- Modify: 对应 Feature 测试文件

- [x] 为纯图标操作、截断文本和固定布局补充或更新失败断言。
- [x] 迁移管理、配置、查看和删除动作到 `TableActionButton`。
- [x] 迁移名称、描述、ID 和状态详情到 `TruncatedText`。
- [x] 运行四个 Feature 的聚焦测试并通过。

### Task 4: 配置和系统列表

**Files:**
- Modify: `apps/web/src/features/browser-profiles/browser-profile-list.tsx`
- Modify: `apps/web/src/features/environments/environment-list.tsx`
- Modify: `apps/web/src/features/model-configs/model-config-list.tsx`
- Modify: `apps/web/src/features/test-accounts/test-account-list.tsx`
- Modify: `apps/web/src/features/users/user-management.tsx`
- Modify: 对应 Feature 测试文件

- [x] 为操作按钮尺寸、图标语义和长值截断补充失败断言。
- [x] 迁移行操作并移除操作列中的可见文字。
- [x] 为名称、地址、掩码凭证、邮箱等长字段增加完整文本 Tooltip。
- [x] 运行五个 Feature 的聚焦测试并通过。

### Task 5: 其余集合与详情子表

**Files:**
- Modify: `apps/web/src/features/experiments/experiment-list.tsx`
- Modify: `apps/web/src/features/gates/gate-list.tsx`
- Modify: `apps/web/src/features/scorers/scorer-list.tsx`
- Modify: `apps/web/src/features/datasets/dataset-detail.tsx`
- Modify: `apps/web/src/features/projects/project-overview.tsx`
- Modify: `apps/web/src/features/runs/trace-comparison.tsx`

- [x] 盘点这些集合中的用户输入长值和行级操作并补充回归断言。
- [x] 卡片操作迁移为共享图标按钮；只读子表使用固定布局和截断文本。
- [x] 运行对应聚焦测试并通过。

### Task 6: 全量和视觉验证

**Files:**
- Create: `apps/web/tests/e2e/list-layout.spec.ts`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [x] Playwright 路由稳定数据，在 1280、1440、1920、390 视口断言页面无横向溢出、操作可见、Tooltip 和编辑 Dialog 可用。
- [x] 运行 Prettier、ESLint、typecheck、Vitest、Playwright 和 production build。
- [x] 检查截图中无遮挡、错位、空白或文本重叠。
- [x] 更新任务记录、验证证据、遗留问题和下一步，执行 `git diff --check` 后提交。
