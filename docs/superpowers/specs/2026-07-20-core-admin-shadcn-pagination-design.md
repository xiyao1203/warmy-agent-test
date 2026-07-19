# 核心管理后台 shadcn 组件与标准分页设计

## 背景

核心管理后台已经具备统一品牌 Token、共享表格、基础按钮和弹窗，但列表接口分别使用游标、`offset/limit`、固定上限或完整集合，前端也没有统一的标准页码分页。用户、项目、Agent、用例、计划等页面的统计摘要、筛选区、列表表面和业务卡片仍采用不同的局部结构，导致数据量增大后无法稳定翻页，页面状态和交互密度也不一致。

本任务保留 WarMy / GLM 风格、明暗主题、现有业务行为和权限边界，使用 shadcn/ui 的本地代码持有与组合方式统一核心管理后台。登录页和测试 Agent 聊天工作台不在本轮范围。

## 目标

- 所有核心资源列表提供真实服务端页码分页，支持每页 `10 / 20 / 50` 条。
- 分页器统一显示总条数、当前页、总页数、首页、上一页、页码、下一页和末页。
- 统计摘要、筛选工具栏、表格、卡片、详情列表和弹窗使用一致的 shadcn 组件结构与交互状态。
- 分页、筛选和排序状态可通过 URL 恢复，删除、空页和越界场景自动回到有效页。
- 不构建万能业务表格，不削弱各 Feature 对列、筛选、动作和权限的所有权。

## 范围

### 资源与治理模块

- 项目、用户、Agent 与版本。
- 用例集、用例与版本。
- 测试计划与版本、测试执行与结果列表。
- 环境与凭证、浏览器实例、模型配置和测试账号。
- 评分器、实验对比、人工审核、安全扫描和发布门禁。
- 上述页面中的统计摘要、筛选区、业务卡片、详情列表和弹窗。

### 非目标

- 登录页、产品落地页和测试 Agent 聊天工作台。
- 新增业务字段、改变权限、项目隔离、发布版本或执行规则。
- 把所有业务列表抽象为一个配置驱动的万能 DataTable。
- 全面替换品牌色、主题 Token、字体或导航架构。
- 为本轮没有产品需求的列表新增排序、列显隐或批量操作。

## 分页契约

### 请求

新页码模式统一使用：

- `page`：从 1 开始的页码。
- `page_size`：仅允许 10、20、50。
- 模块已有的搜索、状态、类型和排序参数继续独立传递。

API 将 `page` 和 `page_size` 声明为可选参数。调用方显式传入任一参数时进入页码模式：缺少 `page` 时按 1 处理，缺少 `page_size` 时按 10 处理；两者均未传入时继续使用现有 `cursor`、`limit` 或 `offset` 语义，避免改变已有内部调用和外部消费者的默认条数。新 Web 列表始终显式传入两个参数。

### 响应

核心列表响应统一包含：

- `items`
- `total`
- `page`
- `page_size`
- `total_pages`
- 原响应已有的 `next_cursor` 暂时保留；旧游标模式继续返回真实值，页码模式返回 `null`

总数为当前项目、权限范围和筛选条件下的真实总数，不是当前已加载集合的长度。空集合的 `total_pages` 为 0，前端显示第 0/0 页且禁用翻页操作。

### 后端边界

- Domain 只保留业务实体和值对象，不依赖分页 DTO 或 ORM。
- Application 定义分页查询输入和结果 Port。
- Infrastructure Repository 使用稳定排序和唯一键作为并列排序兜底，分别执行分页查询与总数统计。
- API 负责查询参数校验和响应翻译，不直接操作 ORM。
- 所有项目资源的分页与总数查询必须同时校验 `project_id`；全局用户列表继续由系统权限门禁保护。
- 计数查询复用已有筛选条件与索引，不引入无界预加载。

## 前端状态与数据流

共享 `usePaginationState` 管理 `page`、`pageSize` 和 URL 同步。单列表页面使用 `page` / `pageSize`；同页多列表使用稳定命名空间，避免查询参数冲突。

分页字段进入 TanStack Query Key。切换页码时保留上一页数据并在列表区域显示局部加载状态；搜索、筛选、排序或每页条数改变时重置到第一页。删除当前页最后一条后重新计算有效页并回退；服务端返回越界页时自动替换 URL 并请求最后一页。

共享分页器只接收受控状态：`page`、`pageSize`、`total`、`totalPages` 和变更回调。它不持有业务查询，不依赖具体 Feature，也不要求业务列表迁移到统一列配置。

## shadcn 组件层

采用 shadcn/ui 的“组件源码由项目持有”方式，不使用 CLI 批量覆盖现有组件。增加合法的 `components.json` 以固定路径和未来受控导入；新组件继续位于 `apps/web/src/components/ui`，不依赖 Feature。

若 `Select` 需要 Radix Select，则把 Lockfile 中已经解析的 `@radix-ui/react-select@2.3.2` 提升为 Web 直接固定依赖，不引入浮动版本或额外组件框架。Card、Pagination 和布局组件使用本地源码，不新增运行时依赖。预计无数据库迁移。

共享组件包括：

- `Card`、`CardHeader`、`CardTitle`、`CardDescription`、`CardAction`、`CardContent`、`CardFooter`。
- `Select` 及其触发器、内容和选项。
- `Pagination` 基础原语与受控 `ResourcePagination`。
- `ListToolbar`、`SummaryStrip` 和列表状态容器。
- 继续复用并扩展现有 `Button`、`Input`、`Badge`、`Table`、`Dialog`、`Drawer`、`Tooltip` 和 `TableActions`。

组件使用现有语义 Token 和品牌色；不把 shadcn 默认黑白配色直接写入页面。Card 最大圆角保持 8px，不创建卡片嵌套，不把普通页面分区做成漂浮卡片。

## 页面结构与交互

核心列表统一为：

1. `PageHeader`：标题、说明和主操作。
2. `SummaryStrip`：摘要指标和分隔线；不是包裹整页的卡片。
3. `ListToolbar`：自适应搜索、筛选和明确命令。
4. 列表内容：桌面表格或业务资源卡片。
5. `ResourcePagination`：列表底部的标准分页器。

桌面端显示总数、每页条数、首页/末页、上一页/下一页和紧凑页码窗口。移动端保留每页条数、上一页、当前页和下一页，隐藏低优先级列或使用现有紧凑卡片，禁止页面级横向溢出。

图标型操作维持 32px 稳定点击区域、Hover/Focus Tooltip、完整 `aria-label`、禁用状态和危险操作确认。异步列表提供稳定高度的 Skeleton、表格内空状态、错误说明与重试，不因切页使整个页面闪烁。

## 模块迁移规则

- 每个 Feature 保留自己的 API Query、列定义、筛选状态、权限判断和动作回调。
- 列表页面只组合共享 UI 和受控分页状态，不复制页码计算或 page-size 校验。
- 详情页的版本、用例或结果子列表遵循同一分页契约；同页多列表使用独立 URL 命名空间。
- 无服务端分页的模块补齐 Repository/Application/API 链路；已有游标或 offset 分页的模块增加兼容页码模式。
- OpenAPI 与生成客户端必须和后端契约同一任务更新，前端不得手写重复 DTO。

## 异常与边界场景

- 非法 `page`、非法 `page_size`：API 返回标准 422 问题响应。
- 页码超出总页数：前端归一到最后一页；空集合归一到第 1 页请求、0 页展示。
- 过滤后无结果：保留筛选条件，显示明确空状态，不回退到未过滤数据。
- 删除最后一条：失效相关 Query 后请求上一有效页。
- 请求失败：保留上一次可见内容并显示局部错误和重试；首次请求失败显示完整错误状态。
- 权限和项目隔离错误继续使用现有错误转换，不通过分页逻辑吞掉 403/404。

## 测试与验收

### 后端

- Repository 测试覆盖总数、稳定排序、边界页、空集合和筛选条件。
- Application/API 测试覆盖 `10 / 20 / 50`、非法大小、页码越界、旧参数兼容和项目隔离。
- OpenAPI 与生成客户端重新生成并通过零漂移检查。

### 前端

- 共享组件测试覆盖 Card 组合、分页窗口、首尾/上下页、每页条数、移动精简和无障碍名称。
- Feature 测试覆盖 Query Key、URL 恢复、筛选重置、切页保留数据和删除回页。
- 架构测试阻止核心列表绕过共享分页器、复制分页算法或手写 API 分页 DTO。

### E2E 与质量门禁

- Playwright 覆盖用户、项目、Agent、用例、计划和执行列表的翻页、`10 / 20 / 50`、筛选重置和刷新恢复。
- 在桌面、390px 移动端、浅色和深色主题验证布局、焦点、Tooltip、空状态和无横向溢出。
- 运行前后端 format、lint/ruff、typecheck/mypy、单元/组件/集成/API/架构测试、生产构建、Bundle Budget 和关键 Playwright E2E。
- 未运行的验证必须写入开发记录并说明原因与风险，不能推测通过。

## 参考

- shadcn/ui Data Table：`https://ui.shadcn.com/docs/components/base/data-table`
- shadcn/ui Card：`https://ui.shadcn.com/docs/components/base/card`
- shadcn/ui Pagination：`https://ui.shadcn.com/docs/components/radix/pagination`
- shadcn/ui components.json：`https://ui.shadcn.com/docs/components-json`
