# 业务与技术架构边界收敛设计

## 1. 背景与结论

平台已采用模块化单体控制面、独立 Worker、Temporal 编排和 Feature 化前端，现有架构门禁也能阻止跨模块内部导入、Domain 引入框架以及 API 直接访问 ORM。当前审计仍发现少量同模块反向依赖没有被门禁覆盖：

- `feedback.domain` 依赖 `feedback.api` 的枚举。
- `feedback.application` 依赖具体 SQLAlchemy Repository 和 API Schema。
- `user_settings.application` 依赖具体 SQLAlchemy Repository。
- 报告格式生成器由 API 直接实例化，技术适配职责没有通过 Application Port 注入。
- 当前扫描器没有系统检查同模块 `Domain → API/Infrastructure`、`Application → API/Infrastructure`，也没有覆盖 Worker/插件对控制面内部包和数据库驱动的反向依赖。

本任务采用“边界加固”方案，不做全仓目录搬迁或微服务拆分。业务规则留在 Domain/Application，数据库、格式渲染和外部运行时留在 Infrastructure，API/Bootstrap 仅负责协议转换和装配。

## 2. 备选方案与选择

### 方案 A：定向边界加固（采用）

修复已识别的反向依赖，增强 AST 架构门禁，保留现有部署、接口、表结构和业务行为。优点是变更面可控、回归证据明确，并能防止相同问题再次出现。

### 方案 B：强制所有模块统一目录并整体搬迁

将单文件 Facade、纯领域工具和报告模块全部改造成同样的四层目录。形式更整齐，但会产生大量无业务价值的移动、导入改写和合并冲突，不能提高运行正确性，因此不采用。

### 方案 C：直接拆分微服务

把项目、用例、运行、评测等拆成独立服务。当前尚无独立扩容、团队、合规或发布边界，拆分会引入分布式事务、契约版本和运维成本，因此不采用。

## 3. 不可变兼容性边界

本任务必须满足以下零漂移条件：

- 不改变任何页面路由、文案、交互和可见权限。
- 不改变 `/api/v1` 路径、请求字段、响应字段、状态码和媒体类型。
- OpenAPI 与生成客户端保持零差异。
- 不新增或修改 Alembic 迁移、数据库表、约束、索引和历史数据。
- 不改变项目隔离、角色权限、状态机、幂等键和审计语义。
- 不改变 Temporal Workflow/Activity 名称、载荷、重试、取消和恢复语义。
- 不改变插件 SDK、Worker DTO、Artifact 和专业测试用例快照格式。

## 4. 目标依赖规则

```text
API / Bootstrap / Worker Entry Point
                 ↓
             Application
                 ↓
               Domain

Infrastructure ──implements──> Application/Domain Port
```

具体约束：

1. Domain 不得依赖同模块或其他模块的 Application、API、Infrastructure，也不得依赖 FastAPI、SQLAlchemy、Redis、Temporal 和厂商 SDK。
2. Application 不得依赖同模块或其他模块的 API、Infrastructure，也不得直接依赖 FastAPI、SQLAlchemy、Redis、Temporal；外部能力通过 `Protocol` Port 注入。
3. API 可依赖 Domain/Application 的公开类型，但不得依赖 Infrastructure、SQLAlchemy 或直接执行持久化。
4. Infrastructure 可向内依赖 Domain/Application 并实现 Port。
5. 跨业务模块只能依赖目标模块的 `public.py`；Bootstrap 作为 Composition Root 可以装配各层具体实现。
6. Worker 和插件不得导入 Control API 内部模块，不得引入 SQLAlchemy、psycopg 或 asyncpg 连接业务数据库。
7. 纯 Domain/Application Facade 可以保留单文件布局；边界由依赖规则而不是目录形式主义判断。

## 5. 模块迁移设计

### 5.1 Feedback

- 将 `FeedbackType` 移到 Domain value object，API Schema 仅引用该类型。
- 在 Application 定义 `FeedbackRepository` Port。
- `CreateFeedbackHandler` 只依赖 Port 和 Domain，不认识 SQLAlchemy 或 Pydantic Schema。
- SQLAlchemy Repository 实现 Port；Router 和响应契约保持不变。

### 5.2 User Settings

- 在 Application 定义 `UserSettingsRepository` Port。
- Query/Command Handler 只依赖 Port。
- SQLAlchemy Repository 实现 Port；默认值、更新语义和 API响应保持不变。

### 5.3 Reports

- Application 定义结构化 `RunReport`/`RunCaseReport` DTO 与报告 Renderer Port，避免散布 `dict[str, Any]`。
- JSON、JUnit 和 HTML 生成器作为 Infrastructure Renderer，实现相同 Port。
- Application Export Service 根据受控格式选择 Renderer；API 只处理认证、错误映射、Content-Type 与 Response。
- 输出内容、下载格式、状态码和媒体类型保持兼容；生成时间继续由 Renderer 负责。

### 5.4 自动架构门禁

- 扩展 `scripts/check_architecture.py` 检测同模块和跨模块的反向层依赖。
- 增加 Application 禁止框架/Infrastructure/API 的测试。
- 增加 Domain 禁止 API/Application/Infrastructure 的测试。
- 增加 Worker/插件禁止 Control API 内部依赖和业务数据库驱动的扫描。
- 保留 Bootstrap Composition Root 合法装配能力，不将目录整齐度误判为架构正确性。

## 6. 数据流与错误处理

HTTP 请求仍由 Router 完成认证、CSRF、Pydantic 校验和 Problem Details 映射。Router 调用 Application Handler/Service；Application 只操作 Domain 和 Port；Bootstrap 注入 Infrastructure 实现。原有异常类型、HTTP 状态码和用户可见内容保持不变。

数据库事务边界、Repository 查询和持久化语句不改变。报告导出的业务数据读取仍通过 Runs/Projects 的公开 Application 接口，只有格式渲染职责迁入 Infrastructure。

## 7. 测试策略

采用 TDD：

1. 先增加架构测试，确认它能对当前反向依赖按预期失败。
2. 逐个模块引入 Port/DTO 并迁移依赖，每完成一个模块运行该模块单元/API测试。
3. 为 JSON/JUnit/HTML 报告增加兼容性快照或结构断言，证明格式未改变。
4. 运行后端、前端、Worker、插件和 OpenAPI 全量门禁。
5. 使用真实 PostgreSQL 覆盖迁移、项目隔离、约束和 Repository 集成；本任务预期 Schema 零变化。
6. 完整 Playwright 验证关键用户旅程没有回归。
7. 最终独立复审重点检查隐藏行为变化、边界遗漏和门禁误报。

## 8. 完成标准

- 当前扫描范围内不存在 Domain/Application 反向依赖。
- Worker/插件不存在 Control API 内部导入或业务数据库驱动依赖。
- `make architecture`、`make verify`、`make performance`、`make security-audit` 通过。
- PostgreSQL、Workflow replay/Worker、完整 Playwright 和 OpenAPI 零漂移通过，或对环境条件跳过项记录明确证据与风险。
- API、数据库、前端、Workflow 和插件契约无变化。
- 任务台账记录实际文件、测试结果和遗留项。
