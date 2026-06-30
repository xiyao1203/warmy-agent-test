# 生产路径真实性清理设计

## 1. 背景与目标

仓库已具备模型配置、运行、浏览器、安全扫描、报告和测试 Agent 等能力，但审计发现部分生产路径仍会返回预设结果、把依赖缺失当作跳过、使用内存保存业务事实，或把开发默认值带入运行时。此类行为会制造“功能成功”的错觉，并破坏可复现性、数据隔离和审计可信度。

本任务的目标不是删除平台支持的测试替身，而是建立清晰边界：用户主动配置的网络 Mock、故障注入、测试代码中的 Fake Target 属于正式测试能力；生产服务自动选择 Mock、返回演示数据、静默降级或伪造完成状态属于缺陷。

## 2. 审计结论

必须修复：

- API Runner 在 Playwright 缺依赖时返回 `skipped`，Browser Harness 缺依赖时返回空快照，调用方没有把采集错误计入用例失败。
- 安全扫描在 Promptfoo 不存在时自动改用预设漏洞结果，且未要求真实 Agent endpoint。
- 报告导出路由忽略数据库，固定返回 `demo-project` 和示例用例。
- 从失败运行生成用例固定创建一条模板用例，既不读取 RunCase，也不持久化生成结果。
- 测试 Agent 会话和 Playwright Agent 任务使用进程内字典，重启即丢失。
- Playwright Planner/Generator/Healer 后端仅执行初始化或普通测试命令，用户 prompt 未进入 Agent 循环，非零退出码也可能被标记为完成。
- 多个前端 Feature 重复定义带 localhost 默认值的 Control API 地址，生产构建缺配置时会指向访问者本机。
- Compose 使用浮动镜像标签，CORS 固定放开所有来源，内部 Token 和本地凭证存在可被误带入非本地环境的默认值。

保留：

- `NetworkMockManager` 和环境模板中的 Mock 服务配置，因为这是用户显式启用的待测环境能力。
- 单元测试中的 Mock/Fake、Worker Fake Target、示例域名输入提示、协议规定的状态与枚举常量。
- 本地开发 README 中明确标注的 localhost 示例，但生产运行时不得静默使用这些值。

## 3. 总体方案

采用“生产真实性清理”方案：所有生产执行路径遵循 fail-closed；业务数据来自项目隔离的 PostgreSQL；可选依赖缺失产生可分类错误；运行时配置集中校验；仓库增加可维护的审计门禁防止同类问题回归。

不采用全局字符串清零方案，因为它会误删产品的 Mock 测试能力和测试替身；不采用只处理模型链路的窄范围方案，因为报告、安全扫描和浏览器执行仍会产生错误事实。

## 4. 详细设计

### 4.1 Worker fail-closed

删除 Playwright `_mock_result`。Playwright 或 Browser Harness 依赖不可用时抛出可分类、不可重试的依赖错误；目标导航或浏览器执行错误保留为真实 `error`。Workflow 对可选预采集的失败不再忽略，而是把当前 RunCase 标为 `error`，错误类型和信息进入回调结果。

### 4.2 安全扫描

删除 `MockScanner` 及自动选择工厂。`PromptfooScanner` 是唯一 MVP 扫描实现，二进制路径由设置注入；启动前缺依赖时扫描记录转为 `failed`。触发请求必须提供或解析真实 Agent endpoint，缺少目标返回校验错误。Promptfoo 非零退出、超时和无效 JSON 都是扫描失败，不能转换成漏洞发现。

### 4.3 真实报告

报告端点改为项目作用域，并通过 Run 应用查询读取 `Run` 与 `RunCase`。不存在或跨项目访问统一返回 404。JSON、JUnit 和 HTML 只使用真实状态、计数、时间、错误和用例名称；HTML 对业务文本进行转义，防止报告中的不可信输出形成注入。

### 4.4 从失败运行生成用例

应用服务接收项目作用域 Run 查询端口和现有 `AddTestCase` 能力。它验证目标数据集版本仍是草稿、Run 属于同一项目，只读取 `failed`/`error` RunCase，并把真实 `input_snapshot`、名称和失败上下文转为新用例。重复来源通过稳定标签/元数据去重，所有新用例实际写入数据库并记录审计。

### 4.5 测试 Agent 会话

新增 `test_agent_sessions` 与 `test_agent_messages` 表，所有记录带 `project_id`，消息按会话和序号唯一。Repository 负责保存会话、追加消息和按项目读取。确认操作仅把草稿状态改为 `confirmed`；在尚未建立测试计划资产转换链路前，不再返回“已开始执行”的假消息。

### 4.6 移除伪 Playwright Agent 入口

删除控制面的 Planner/Generator/Healer 适配器、API、任务字典和前端面板，同时同步 OpenAPI 与生成客户端。保留确定性 Playwright Runner。Playwright 官方 Agent 定义需要由 Codex 等 AI 工具继续驱动，并不是可直接作为后端 Agent API 调用的运行时；未来若恢复该能力，必须作为独立 Worker 接入项目模型配置、浏览器工具循环、Artifact 和 Temporal。

### 4.7 配置与依赖

前端只从共享 API Client 读取唯一 base URL；本地开发使用文档化地址，生产未配置外部地址时使用同源相对请求，绝不回退到访问者本机。后端 CORS 使用 `web_origin`，非 `local` 环境禁止默认内部 Token。Promptfoo、Temporal、MinIO 与 Playwright 相关版本固定到仓库验证过的精确版本，Compose 本地凭证继续允许环境变量默认值，但在文档中明确仅限本地。

### 4.8 审计门禁

新增生产真实性检查脚本和测试，扫描生产源码与部署配置中的已知风险模式：自动 Mock 工厂、演示项目数据、伪成功注释、浮动镜像、Feature 自建 API base URL。允许列表只包含网络 Mock 产品模块、测试目录和明确的 UI placeholder 属性。

## 5. 数据与迁移

新增 Alembic `0010`：

- `test_agent_sessions(id, project_id, status, plan_draft, created_by, created_at, updated_at)`。
- `test_agent_messages(id, session_id, project_id, sequence, role, content, created_at)`。
- 会话使用 `(project_id, id)` 唯一约束；消息使用复合外键 `(project_id, session_id)`，并建立 `(project_id, session_id, sequence)` 唯一约束和读取索引。
- 删除项目时级联删除会话与消息；用户只保留创建者引用。

迁移不修改既有 `0001` 至 `0009`。

## 6. API 变化

- 保留测试 Agent chat、confirm、session 查询路径，但实现改为持久化，并修正确认响应语义。
- 删除 `/test-agent/playwright/execute` 和 `/test-agent/playwright/tasks*`。
- 报告改为 `/api/v1/projects/{project_id}/runs/{run_id}/export?format=...`。
- 安全扫描触发体包含真实 `agent_endpoint` 与 `scan_type`。
- 从失败运行生成用例返回真实 `generated`、`total_failed` 与 `skipped_existing`。

OpenAPI 和 TypeScript Client 与代码同步，不保留已删除端点的兼容假实现。

## 7. 错误处理与安全

- 依赖缺失：503 或 Worker `DependencyUnavailable`，不得返回成功/跳过。
- 外部工具失败：保存失败状态和脱敏摘要，不回传 Token、Cookie、完整凭证或任意 stderr。
- 项目隔离：所有会话、报告、RunCase 和生成用例查询必须带 `project_id`。
- 报告输出：HTML 转义，JSON/JUnit 使用安全序列化。
- 外部 URL：沿用模型配置的私网限制原则，安全扫描目标需要 URL 校验并受项目配置控制。

## 8. 验收标准

- 生产源码不存在自动 Mock 回退、演示报告、固定生成用例或内存业务事实源。
- 缺 Playwright、Browser Harness、Promptfoo 或运行时配置时明确失败。
- 测试 Agent 会话跨应用实例可读取且项目隔离。
- 报告和失败用例完全来自真实 Run/RunCase。
- 伪 Playwright Agent API/UI/OpenAPI 已移除。
- 前端 API 地址单一来源，生产缺配置使用同源请求而非 localhost。
- Compose 不使用浮动镜像标签。
- 新增回归测试、迁移测试、OpenAPI 漂移检查和全仓质量命令均有真实执行记录。
