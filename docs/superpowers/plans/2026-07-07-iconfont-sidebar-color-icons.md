# iconfont 风格侧边栏彩色 SVG 图标替换计划

## 背景

用户反馈当前侧边栏图标仍然太丑，主要问题是视觉仍像 lucide 线框图标加粗叠色，不像 iconfont 上的时尚彩色图标。

已查看 iconfont：

- 多色图标库：`https://www.iconfont.cn/collections/index?type=2`
- `211-多彩亚克力常用`：色彩鲜明、扁平几何、适合导航小图标。
- `网络安全毛玻璃质感图标库`：科技与安全语义更贴近平台，但颜色偏淡，直接照搬不适合深色侧栏。

## 目标

将侧边栏项目导航和系统管理图标替换为一套本地 SVG 彩色图标资产：

- 不再使用 lucide 图标作为导航图标本体。
- 不再使用角标、外框、胶囊底或叠线框。
- 每个图标使用 3 到 5 个彩色 SVG 图形元素表达业务语义。
- 风格参考 iconfont 多色集合，但不直接复制未明确授权的第三方 SVG 源码。

## 实施步骤

1. 在组件测试中先锁定新期望：导航图标应为 `iconfont-color` 风格、本地 SVG artwork、非 lucide 叠色结构。
2. 新建 `apps/web/src/components/layout/sidebar-icons.tsx`，集中维护图标名称、色板和 SVG artwork。
3. 在 `app-shell.tsx` 中移除导航项的 lucide 图标导入，改用本地 `SidebarColorIcon`。
4. 保留 `PanelLeft*` 和 `Search` 等非侧边栏导航图标的现有实现。
5. 更新开发记录和当前任务。

## 验证

- `pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx`
- `pnpm --filter @warmy/web exec eslint src/components/layout/app-shell.tsx src/components/layout/app-shell.test.tsx src/components/layout/sidebar-icons.tsx`
- `pnpm --filter @warmy/web typecheck`
- `pnpm --filter @warmy/web build`
- `pnpm --filter @warmy/web exec playwright test tests/e2e/login.spec.ts --config=playwright.config.ts`
- `git diff --check`
