# 全仓热点收敛与数据访问统一设计规格

## 1. 背景

前一轮已经完成专业测试资产、GLM Coding 风格前端和 Domain/Application/API/Infrastructure 边界收敛，并通过全量质量、性能、安全、PostgreSQL、Worker 和 Playwright 门禁。本轮不再改变产品形态或核心架构，而是处理仍然影响开发效率、回归稳定性和长期演进的实现热点。

只读审计确认以下事实：

- `bootstrap/wiring.py` 约 2300 行，与现行 Registrar 装配重复；生产入口使用 `bootstrap/app.py`，仅 `BootstrapContext` 仍从遗留文件读取 Auth Builder，性能测试借其副作用加载 ORM Metadata。
- `bootstrap/core_summaries.py` 约 1100 行，集中维护 11 类核心列表查询；固定查询数已经有性能门禁，但文件职责和依赖面过大。
- `test_agent/adapters/platform.py` 约 1300 行，同时承载资产、执行、质量和发布能力映射。
- Web 的 Chat Workspace、Agent 详情/版本、专业用例编辑和计划编辑等组件达到 700–1200 行；部分 Screen 同时管理请求、版本状态、缓存刷新和 View Props。
- 核心 Feature 混用 OpenAPI 生成 SDK、手写 `fetch`、手写响应类型和直接 `refetch`，同一资源的 Query Key 还存在用途后缀，容易造成缓存重复或失效遗漏。
- 完整 Playwright 首轮曾被 Git 忽略目录中的 4.5 GiB Turbopack 开发缓存和残留构建锁阻塞，说明 E2E 构建产物仍与日常开发目录耦合。

## 2. 目标与成功标准

本任务必须同时满足：

1. 删除不再承担生产装配职责的遗留 `bootstrap/wiring.py`，生产和测试统一使用 Registrar/Provider 组合根。
2. 保持 `SqlAlchemyCoreSummaryReader` 和 Test Agent 平台公开能力不变，将内部实现拆成职责单一、可独立测试的单元。
3. 核心 Web Feature 的普通 JSON API 使用生成 SDK；原始 `fetch` 只保留 SSE、流式下载或生成 SDK 无法表达的协议，并有显式 Allowlist 测试。
4. Feature 自己拥有 Query Key/Options 与 Mutation 失效策略；相同资源不因页面用途生成互不相干的缓存键。
5. 大型组件拆分后页面视觉、文案、DOM 可访问语义、路由和交互结果不变，页面文件只负责编排。
6. E2E 的数据库、Next 构建目录和服务进程均位于一次性 Runtime Directory，成功、失败、取消和超时都清理。
7. OpenAPI、生成客户端、数据库 Schema、权限、项目隔离、Workflow 载荷和产品行为零漂移。

## 3. 非目标与硬约束

- 不新增产品功能、页面、路由、字段、状态或视觉样式。
- 不新增或升级依赖，不创建数据库迁移，不提高性能预算。
- 不为追求目录整齐拆分纯领域小文件，不建立通用 Service Locator 或全局状态仓库。
- 不引入 Redis/进程内业务缓存，不做缺少 `EXPLAIN ANALYZE` 或查询预算证据的索引优化。
- 不修改真实 TapNow 外部执行范围、凭证、账号或额度。
- 不以 `type: ignore`、禁用规则、跳过测试或兼容分支掩盖问题。

## 4. 后端设计

### 4.1 统一组合根

新增按职责组织的 Bootstrap Provider：Identity Provider 负责 Auth/Admin 依赖，运行时上下文直接依赖该 Provider。ORM Metadata 使用显式 Model Registry 加载，不再借由导入整个遗留装配文件产生副作用。

完成替换后删除 `bootstrap/wiring.py`。`bootstrap/app.py` 的 `create_app` 参数、`AppOverrides`、Registrar 顺序、中间件、路由和测试覆盖方式保持不变。架构测试禁止重新导入或创建第二套全量应用装配入口。

### 4.2 Core Summary 查询拆分

保留共享 Application 的 `CoreSummaryReader` Protocol 和 `SqlAlchemyCoreSummaryReader` 对外名称。Infrastructure 实现改为 Facade，委托给以下内部查询组：

- 资产：Project、Agent、Dataset、Test Plan、Environment。
- 执行：Run、Experiment。
- 质量：Scorer、Security Scan、Review、Gate。
- 公共 Lookup：用户、资源引用、最新版本和批量计数。

每个公开方法继续接收 `project_id` 与 ID 集合，继续一次批量返回 Map。现有固定 SQL 查询数是上限，不允许因拆分增加查询；空 ID 输入不得访问数据库。

### 4.3 Test Agent 平台适配拆分

现有 Platform Adapter 继续作为测试 Agent 的单一公开 Facade，但能力实现按资产、执行、质量/发布拆分。每个子适配器只依赖所需公开 Application 能力；Facade 仅注册能力并转发，不复制平台 DTO 转换逻辑。

能力名称、输入 Schema、输出资源引用、排序、分页、项目隔离和审计语义保持不变。现有能力目录和列表摘要测试作为兼容契约。

### 4.4 类型边界

对数据库 JSON、插件结果、Worker 回调和模型输出使用集中解析函数、TypedDict 或 Pydantic Application DTO，再交给 Domain。可选依赖缺少类型声明的 `import-not-found/import-untyped` 例外可以保留，但业务数据转换中的 `arg-type/assignment/misc` 忽略必须在本任务触及范围内消除。

## 5. 前端设计

### 5.1 API 访问

普通 JSON HTTP 端点直接调用 `@warmy/generated-api-client` 导出的 SDK，并统一传入 `apiClient`、CSRF Header 与 `throwOnError`。Feature 不再手写已经存在于 OpenAPI 的请求/响应类型。

仅以下协议允许使用原始 `fetch`：

- SSE 或其他增量流。
- 文件上传/下载中生成 SDK 无法保留流语义的端点。
- 浏览器导航或第三方 URL，而非 Control API JSON。

原始请求必须复用 `CONTROL_API_URL`、`csrfHeaders` 和 `responseProblem`，不得自行吞掉 Problem Details。

### 5.2 TanStack Query 所有权

每个 Feature 在公开出口提供本 Feature 的 Query Key/Options 工厂。Key 按资源层级组织，例如 Project → Dataset → Version → Cases，不使用 `test-case-trial` 等页面用途字符串制造第二份相同资源缓存。

Mutation 成功后通过 `queryClient.invalidateQueries` 或精确 `setQueryData` 更新事实源；只有需要立即返回刷新结果的动作才能显式 `refetch`。Query Function 接收 AbortSignal 并传给生成 Client，路由切换时可取消无效请求。

### 5.3 组件拆分

优先拆分超过 700 行且同时承担数据、状态和展示的热点：Chat Workspace、Agent 详情/版本、专业用例编辑、测试计划版本和 App Shell。拆分遵循：

- `*-screen`：路由参数、Query/Mutation 和页面状态编排。
- `use-*`：业务交互、缓存更新和状态机。
- `*-section`/`*-panel`：纯展示与受控输入。
- `*-model`：无 React 的格式化、校验和 View Model。

不以行数作为唯一目标；拆出的单元必须有清晰输入输出并降低依赖面。现有可访问名称、键盘行为、焦点管理、主题 Token 和 DOM 语义不能变化。

## 6. E2E 与性能可靠性

`next.config.ts` 允许由测试专用环境变量指定 `distDir`，生产默认仍为 `.next`。`start_e2e_server.sh` 在一次性 Runtime Directory 下创建数据库和 Next 产物，并让 `next build` 与 `next start` 使用同一目录；退出钩子删除该目录和子进程。

新增脚本测试覆盖：已有 `.next` 锁或大型开发缓存不会被 E2E 读取；构建失败和信号退出仍清理临时目录。Bundle/Chunk 和 SQL 查询预算保持现有阈值。只有测量证明重复请求、查询数或 Bundle 下降时才记录性能收益，不做推测性声明。

## 7. 错误、安全与兼容性

- SDK 错误统一转换为现有用户可理解文案，保留 401/403/404/409/422 分类。
- 前端缓存不得保存凭证明文；Query Key 不包含 Token、Cookie、Prompt 或输入数据。
- 拆分不得绕过后端权限；所有项目资源仍由服务端按 `project_id` 校验。
- Model Registry 只导入 ORM Metadata，不创建连接、不运行查询、不产生业务对象。
- 插件、Worker、Workflow、数据库和 HTTP 契约不因本任务改变。

## 8. 测试策略

实施按 TDD 推进：

1. 为遗留 Wiring 引用、隐式 Metadata 注册和重复组合根增加失败架构测试。
2. 为 Core Summary 子 Reader 增加空输入、项目隔离、批量 Map 和固定查询数测试。
3. 为 Test Agent 子适配器增加能力清单、输入输出和错误透传契约测试。
4. 为生成 SDK Allowlist、Query Key 层级、失效范围、取消和 Problem Details 增加前端单元/组件测试。
5. 为拆分组件保留现有交互回归，并补充关键 Hook/Model 测试。
6. 为一次性 Next `distDir` 和退出清理增加脚本测试，再运行完整 Playwright。
7. 最终运行 `make verify`、`make performance`、`make security-audit`、PostgreSQL 条件套件、Worker/Workflow 定向套件、完整 Playwright、OpenAPI/生成客户端零漂移和敏感信息扫描。

## 9. 交付与回滚

任务在独立分支 `codex/whole-repository-optimization-pass-2` 实施。拆分按可独立验证的阶段提交，任何阶段都必须保持公开入口兼容。若某个热点无法在不改变行为的情况下拆分，则保留现有实现并记录证据，不通过兼容层复制第二套逻辑。

回滚只需回退本任务提交；由于没有数据库迁移、API 变化或依赖升级，不需要数据补偿或部署双写。规格、实施计划、验证证据和最终状态同步写入进度台账。
