# 全仓性能、架构、可维护性与安全性治理设计

## 1. 背景与目标

本任务在不改变产品范围和公开业务行为的前提下，对 Web、Control API、必要的 Worker 边界和仓库质量门禁做一次综合治理。交付使用单一开发分支和单一主任务，但内部按可独立验证的阶段推进。

“一次性解决”在本设计中的完成定义是：本次审查确认的全部高风险和中风险问题均被修复或由更强的不变量消除，新增自动测试或静态门禁防止同类问题回归。低风险样式偏好、无证据的微优化和与当前风险无关的全仓重写不进入实现范围。

## 2. 已确认基线

- 分支：`codex/repository-hardening`，从干净的 `main` 创建。
- `make verify` 通过：前端 68 个测试文件、287 个测试；Python 941 个测试通过、7 个按既有环境条件跳过；构建、架构和 OpenAPI 漂移检查通过。
- `apps/control-api/src/agenttest/bootstrap/app.py` 为 2251 行，集中装配大量模块和临时端点注册函数。
- 12 个 API 文件直接依赖模块基础设施实现或 SQLAlchemy；现有架构检查只禁止 API 导入持久化 Model，未覆盖 Repository 和直接 SQL。
- Artifact 用户上传和内部上传一次性读取完整文件，没有配置化大小上限；用户上传只检查当前项目访问权，没有证明 `run_id` 属于同一项目。
- Artifact 表分别外键关联 Project 和 Run，但没有数据库级 `(project_id, run_id)` 组合一致性约束。
- 4 个前端生产组件超过 800 行，最大组件超过 1200 行；若干 Feature 直接导入其他 Feature 的内部 `api` 文件。
- 当前账号锁定只覆盖已存在用户的连续失败；未知账号和来源地址没有统一、跨请求的登录节流策略。
- 构建通过，但仓库没有可复现的前端资源预算门禁。

## 3. 方案选择

采用风险优先的综合治理：先用失败测试固定安全不变量和架构边界，再移动代码，最后建立性能预算并拆分前端热点。相比大爆炸重写，此方案可以在同一分支内一次性交付，同时保留每个阶段可定位、可回滚的验证证据。

不采用只修高危漏洞的方案，因为它无法满足架构和可维护性目标；不采用全仓重新分层，因为当前系统已有 941 个 Python 测试和稳定模块边界，无需为统一形式破坏已验证行为。

## 4. 安全设计

### 4.1 Artifact 上传与下载

Artifact 写入改为应用用例，不再由 API 直接操作 Repository、存储和事务。用例必须先验证 Project、Run 和可选 RunCase 的组合归属，再接收内容并持久化元数据。

- 用户上传默认上限为 64 MiB，内部 Worker 上传默认上限为 256 MiB，均可由强类型配置下调或上调。
- 上传按固定大小分块读取并累计字节数，超过上限立即终止；不得先把无界请求全部读入内存。
- 文件名只保留安全 basename，剔除路径分隔符、控制字符和空名称；存储 Key 由服务端生成，不使用用户路径。
- 文件先写入临时对象，数据库提交成功后转为最终对象；数据库失败或取消时删除临时对象，避免孤儿文件。
- 下载使用受控存储流，不把完整大文件重新读入 Control API 内存。
- 内部令牌使用常量时间比较；错误响应不回显令牌、存储绝对路径或内部异常。
- 数据库通过 Run 上的 `(project_id, id)` 唯一键与 Artifact 的 `(project_id, run_id)` 组合外键强制项目一致性。

### 4.2 登录节流

保留既有用户账号锁定，并新增独立 `LoginThrottle` 应用 Port。节流键使用规范化邮箱和来源地址的单向摘要，不持久化原始密码、Session、完整 IP 或未知邮箱。

- 连续失败采用固定时间窗和封禁时间；成功登录清理对应账号维度记录。
- 默认不信任 `Forwarded`/`X-Forwarded-For`；只有直连来源命中显式配置的可信代理 CIDR 时才读取并规范化转发地址。API 将该来源地址传入登录用例，审计记录使用同一来源值。
- 持久化实现由 Identity 基础设施提供，支持多 Control API 实例共享状态；不使用进程内字典作为生产事实源。
- 达到阈值统一返回现有认证失败响应，不泄露账号是否存在或具体节流维度。
- 新迁移包含过期清理索引；清理可由登录路径限量执行，不引入新的后台任务系统。

## 5. 后端架构设计

### 5.1 API 边界

API 只负责请求解析、认证/CSRF、调用应用用例和 DTO/Problem Details 转换。当前 API 中的 SQL、事务、Repository 构造和业务统计移动到对应模块的 Application 服务；Infrastructure 实现查询 Port。

首批边界覆盖静态扫描命中的全部 12 个 API 文件，涉及 Artifacts、Browser Profiles、Environments、Experiments、Gates、Reviews、Runs、Scorers、Security、Test Accounts 和 Test Plans。迁移后 `modules/*/api` 不得导入 SQLAlchemy 或本模块 Infrastructure。

架构检查扩展为以下自动规则：

- API 禁止导入 `sqlalchemy` 和任何 `.infrastructure` 路径。
- API 禁止调用 `session.execute`、`session.scalar` 或构造 Repository。
- Bootstrap 是唯一允许组合 Application 与 Infrastructure 的位置。
- 现有 Domain 禁止框架依赖和跨模块必须走 `public.py` 的规则继续保留。

### 5.2 应用装配

`bootstrap/app.py` 收敛为应用创建、通用中间件和模块注册清单。每个业务模块在 `bootstrap/modules/<module>.py` 暴露一个装配函数，负责创建该模块的 Repository/Adapter、Application Handler 和 Router Dependencies。

装配模块可以依赖基础设施，但不得承载 SQL 查询、权限规则或业务状态变更。公共的 Actor、CSRF、Project Access 和事务工厂通过显式依赖对象复用，删除当前重复的局部 `actor_for`、`check_project` 和异常字符串判断。

## 6. 前端架构与可维护性设计

所有 Feature 已有 `index.ts`，跨 Feature 依赖统一改从公开出口导入。新增静态检查阻止 `@/features/<name>/<internal>` 和相对路径进入其他 Feature；测试文件默认也遵守，只有同一 Feature 内部测试可读取私有模块。

按职责拆分当前超过 800 行的 4 个生产组件：

- `test-agent/chat-screen.tsx`：页面编排、会话副作用、消息/时间线展示和输入区分离。
- `agents/agent-version-dialog.tsx`：表单状态、执行配置、浏览器配置和提交映射分离。
- `environments/environment-list.tsx`：数据状态、列表、版本/凭证对话框分离。
- `datasets/test-case-editor.tsx`：Schema/映射、断言编辑、执行输入和表单壳分离。

拆分后的状态归属遵循：服务端状态进入现有查询层或 Feature API；表单状态留在 React Hook Form；可分享筛选进入 URL；展示组件不发请求。现有可见交互、文案、路由和 API 契约保持不变。

## 7. 性能设计

性能治理只处理可测量问题：

- Artifact 上传/下载使用有界流，峰值应用内存不随文件大小线性增长。
- 从 API 移出的查询以项目范围和批量读取为基本接口，禁止列表逐项查询；关键项目查询使用现有或新增的项目前缀索引。
- 对 Run 对比、实验统计和列表接口增加查询次数/结果上限测试，避免无界加载。
- 前端拆分保持重型功能按路由或交互动态加载；会话副作用使用稳定依赖和单一订阅，避免重复 SSE/轮询。
- 新增可复现的构建资源报告。以本任务开始时的 `main` 构建产物为基线，关键路由首屏 JavaScript gzip 体积不得增加超过 5%；任何单个新增同步 chunk 不得超过 250 KiB gzip。
- Playwright 对登录、项目列表、测试 Agent 和运行中心采集导航时序；本地稳定环境中三次中位数不得比基线退化超过 10%。该门禁比较同机同进程的基线与候选，避免使用绝对网络时间判定。

## 8. 数据与迁移

预计新增两类 Schema 变化：

1. Run/Artifact 项目组合外键和支持该约束的唯一键。
2. Identity 登录节流记录及过期清理索引。

迁移遵循 Expand -> Migrate -> Contract，兼容 SQLite 本地环境和 PostgreSQL 生产环境。必须验证空数据库升级、上一版本升级、已有合法 Artifact 数据保留、非法组合数据检测策略和降级补偿说明。已发布迁移不修改。

## 9. 错误处理与可观测性

- API 统一将认证、权限、资源不存在、大小超限、冲突和内部错误映射为 RFC 7807 响应。
- 安全拒绝记录结构化事件，只记录项目/Run/用户等标识和分类，不记录文件内容、凭证或原始登录秘密。
- 上传中断、存储失败和数据库失败使用不同错误分类；临时对象清理失败可告警但不能伪装上传成功。
- 前端保持统一 Problem Details 转换，错误边界不展示服务端堆栈或内部路径。

## 10. 测试策略

实现严格遵循 Red-Green-Refactor：每个行为先添加能够观察到正确失败原因的测试，再写最小实现。

- Domain/Application：Artifact 组合归属、大小限制、文件名、补偿清理、登录节流窗口和不泄露行为。
- Repository/Migration：真实 PostgreSQL 的组合外键、索引、空库和上一版本升级。
- API Contract：用户/内部上传、下载流、认证、CSRF、跨项目拒绝、413 和 Problem Details。
- Architecture：API 无 Infrastructure/SQLAlchemy、Feature 公共出口、Bootstrap 装配边界。
- Frontend Component：拆分前后关键交互等价、错误/加载/权限状态和副作用单实例。
- Playwright：登录、项目、测试 Agent 和运行中心关键路径及性能采样。
- Supply Chain：Node 生产依赖和 Python 锁文件审计；无法修复的上游问题必须记录版本、影响面和缓解措施。

最终至少运行：`make verify`、独立 PostgreSQL 迁移/隔离套件、关键 Playwright、性能预算、依赖审计、`git diff --check` 和敏感信息扫描。

## 11. 兼容性与回滚

- 公开 HTTP 路径和现有响应字段保持兼容；新增错误仅用于过去未受限的恶意或超限输入。
- 前端只做内部拆分，不改变用户工作流。
- 数据库先增加约束所需索引和新表，不删除旧列；应用回滚后新增表和约束可保留。
- 每个阶段形成单一目标提交；若后续阶段失败，可回滚该阶段而保留已验证的安全修复。

## 12. 非目标

- 不完成需要真实 TapNow 账号、登录态、Codex/Tapies 额度的外部验收。
- 不引入微服务拆分、全新状态管理框架或新的任务编排系统。
- 不重做 UI 视觉设计，不改变 PRD 角色、权限或业务流程。
- 不以删除测试、放宽类型、忽略 Lint 或提高预算阈值掩盖问题。

## 13. 验收标准

- 本设计列出的高、中风险问题均有修复提交和自动化回归证据。
- `modules/*/api` 对 SQLAlchemy 和本模块 Infrastructure 的违规数从 12 个文件降为 0。
- Artifact 的无界内存读取、跨项目 Run 关联和不安全存储路径均被测试拒绝。
- 登录节流覆盖存在账号、未知账号和多实例共享持久化状态，响应不泄露账号存在性。
- `bootstrap/app.py` 只保留顶层应用装配；4 个超过 800 行的前端热点均完成职责拆分，跨 Feature 内部导入为 0。
- 性能预算与依赖审计成为可重复执行的仓库命令。
- 全量质量门禁、独立 PostgreSQL 验证和关键 Playwright 通过；任何环境原因导致的未验证项写入开发记录并标明风险。
