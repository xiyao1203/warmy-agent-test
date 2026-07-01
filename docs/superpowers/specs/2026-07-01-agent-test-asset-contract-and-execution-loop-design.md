# Agent 测试资产契约与完整执行闭环设计

## 1. 目标与原则

本次修复不是为现有表单补充提示，而是统一专业测试控制台的资产契约、配置入口、运行快照和执行消费。

每个模块同时满足两类验收：

1. 独立可用：用户可以在模块页面创建、验证、查看、修改草稿、发布或执行该模块的真实能力。
2. 链路可用：模块通过项目隔离、版本化 ID 和公开应用接口进入完整测试链，不要求用户复制内部 UUID，不产生聊天副本或临时 JSON 事实。

核心链路为：

`AgentVersion + EnvironmentVersion + DatasetVersion + ScorerVersion + SecurityProfile -> TestPlanVersion -> Run -> RunCaseResult + Evaluation -> Experiment / ReviewTask / SecurityScan -> ReleaseDecision`

专业控制台是事实源；超级测试 Agent 只调用同一套公开能力。

## 2. 统一资产状态与引用规则

- 可变配置采用草稿；执行只引用已发布、不可变版本。
- 所有引用必须同时校验 `project_id`、状态和兼容性。
- Web 使用可搜索资产选择器，不暴露“手填 UUID”。
- 列表和详情展示“是否就绪、缺少什么、被哪些计划/运行引用”。
- 删除被引用资产时返回 409 和引用摘要；不静默级联破坏历史。
- Run 保存完整不可变快照，历史结果不依赖后续配置变化。

## 3. 智能体模块

### 3.1 Agent 字段

Agent 只保存身份元数据：

| 字段 | 必填 | 作用 |
|---|---:|---|
| 名称 | 是 | 项目内识别和资产选择 |
| 接入类型 | 是 | `generic_http`、`canvas`，决定适配器和配置 Schema |
| 描述 | 否 | 用途、负责人和测试边界 |

### 3.2 AgentVersion 调用配置

核心配置必须类型化，不再让 UI、RunSource 和 Worker 使用不同字段名：

| 分组 | 字段 | 必填 | 运行时作用 |
|---|---|---:|---|
| 端点 | `endpoint_url` | 是 | Worker 实际请求地址 |
| 协议 | `protocol` | 是 | `sync_json`、`openai_chat`、`sse`、`async_poll` |
| 映射 | `request_template` | 是 | 将用例 input/history 映射成请求体 |
| 映射 | `response_path` | 是 | 从响应中提取规范化 output |
| 映射 | `status_path` / `poll_url_path` | 条件必填 | 异步协议状态和轮询地址 |
| 运行 | `timeout_seconds` | 是 | 单请求超时 |
| 运行 | `max_steps` / `cost_limit` | 否 | Agent 运行限制 |
| 认证 | `credential_binding_ids` | 否 | 引用环境中的加密凭证绑定 |
| 元数据 | model、code/git、prompt/knowledge/tool/adapter 版本 | 否 | 追踪与实验维度，不直接改变 HTTP 协议 |

UI 分为“连接与协议”“请求/响应映射”“运行限制”“版本元数据”四段，并提供：

- 示例请求预览。
- 使用脱敏凭证的真实连接测试。
- 响应提取预览。
- 发布前就绪检查。

旧 `api_url` 数据通过迁移映射到 `endpoint_url`；旧字段只读兼容一个版本周期。

## 4. 环境与凭证模块

环境模板升级为版本化 `EnvironmentVersion`。环境定义非秘密运行上下文，凭证作为独立加密资产被引用。

### 4.1 环境字段

- 名称、描述、适用场景。
- 基础 URL 覆盖和协议覆盖。
- 普通环境变量、非敏感请求头。
- 初始化状态和清理策略。
- Mock/沙箱配置仅在用户主动启用时生效，不作为失败回退。
- 凭证绑定列表：别名、注入位置（Header/Query/Body）、字段名、加密凭证引用。

敏感值写入专用加密凭证表，API 只返回 ID、类型、别名和掩码。Run 快照仅保存引用；Worker 在执行边界按项目和权限解析，日志/Trace 始终脱敏。

模块独立提供“验证凭证”和“测试环境连接”。

## 5. 数据集与测试用例

### 5.1 导入入口

导入必须从具体 Dataset 的草稿 DatasetVersion 发起。无草稿时先创建草稿；已发布版本禁止修改。

UI 提供：模板下载、JSON/JSONL/CSV 示例、字段字典、文件大小限制、客户端预览、服务端 dry-run 预检、逐行错误和导入结果统计。

### 5.2 标准导入契约

必填字段：

- `name`: 非空字符串，版本内用于识别。
- `execution_mode`: `api`、`browser` 或 `canvas`。
- `input`: JSON 对象，必须符合所选 Agent 协议的输入映射前置结构。

可选但有明确作用的字段：

- `assertions`: 结构化确定性断言。
- `expected_outcome`: 参考结果，供 reference/model scorer 使用。
- `scorer_bindings`: 覆盖计划默认评分器。
- `initial_state`: 传给环境初始化器。
- `security_profile_ids`: 指定安全策略。
- `tags/scenario/priority/risk_level/difficulty/test_group`: 筛选、调度、审核和报告维度。

任何字段类型错误必须逐行失败，禁止把错误 input 静默转成 `{}`。同一次导入保持全有或全无。

发布后的 DatasetVersion 可直接被计划选择；Run 快照必须保留全部执行相关字段。

## 6. 评分器模块

评分器采用类型化配置并可独立“试评”：

- Rule：输出路径、运算符、期望值/表达式。
- Reference：输出路径、参考字段、匹配方式和容差。
- Model Judge：项目 ModelConfig 引用、Rubric、评分范围、结构化输出 Schema、置信度阈值。
- 后续视觉/结构评分器通过同一公开协议扩展。

权重只参与 Evaluation 聚合；评分器自身阈值判断单项是否通过。TestPlanVersion 保存 `scorer_binding_ids` 和可选权重覆盖，不保存无类型 scorer JSON。

Worker 在目标 Agent 返回后执行评分 Activity，持久化每个 `Score` 及总 `Evaluation`；模型评分必须走 Model Runner，失败不得伪装为 0 分或通过。

## 7. 测试计划与执行

### 7.1 TestPlanVersion 必选关系

- 一个已发布 AgentVersion。
- 一个已发布 DatasetVersion。
- 一个已发布 EnvironmentVersion。
- 至少一个断言或评分器；纯观测计划必须显式选择“仅采集”。
- 可选 SecurityProfile、ReviewPolicy、ReleaseGate。

### 7.2 执行策略

- 并发、每用例次数、单次超时、最大重试。
- 重试条件和退避策略。
- 预算（Token、成本、总时长）。
- 用例筛选标签和执行模式。

计划编辑器按“资产 → 执行 → 评测 → 安全与发布”分步，并显示引用资产就绪检查和预计用例数。

### 7.3 RunSnapshot

RunSource 构建明确 Schema：

- `agent`: 已发布调用配置快照。
- `environment`: 非秘密配置与凭证引用快照。
- `plan`: 并发、重试、预算和筛选快照。
- `cases`: input、assertions、expected outcome、initial state、scorer/security 覆盖。
- `scorers/security/review/gate`: 版本化策略快照。

API Runner 只消费该 Schema，不再猜测 `url`、`api_url` 或嵌套位置。

## 8. 结果、实验、安全、审核与门禁

### 8.1 Evaluation

Evaluation 聚合确定性断言、各评分器分数、成本、Token、耗时和安全摘要，输出通过状态、置信度和失败原因。它是后续模块的统一输入。

### 8.2 实验对比

实验通过资产选择器选择基线 Run 和候选 Run。系统只允许项目相同、计划/数据集兼容且用例集合可对齐的 Run；不允许手填 UUID。输出逐用例状态、评分、耗时、成本和安全差异。

### 8.3 安全测试

安全扫描选择 AgentVersion、EnvironmentVersion、SecurityProfile 和可选 DatasetVersion/Run，不再手填裸 URL。扫描生成真实 SecurityFinding，并可一键转为回归 TestCase。

### 8.4 人工审核

ReviewPolicy 定义低置信度、评分冲突、高风险和安全发现阈值。Evaluation/SecurityFinding 完成后自动创建去重 ReviewTask。人工决定不可由 Agent 代签，决定写回 Evaluation/ReleaseDecision 来源链。

### 8.5 发布门禁

门禁选择真实 ReleaseGate 和目标 Run/Experiment；服务端聚合通过率、关键用例、成本、安全评分和待审核阻塞项。前端不得提交推测指标，更不得使用固定 `0.85` 或 `true`。评估输出持久化 `ReleaseDecision`，支持有权限、有原因、有审计的豁免。

## 9. 超级 Agent 与专业控制台

超级 Agent 使用与页面相同的公开 Application 能力：

- 读取 Schema 和就绪检查后追问缺失字段。
- 只创建真实草稿资产并返回专业控制台链接。
- 发布、执行、安全扫描、审核决定和门禁豁免仍按风险确认。
- 每个资产保留会话/任务来源，控制台修改后不复制数据。

## 10. 错误、安全和兼容

- 核心配置全部使用版本化 Pydantic/领域 Schema；未知字段拒绝或显式迁移。
- 供应商、目标 Agent、评分器或安全工具失败时保存明确失败，不生成占位结果。
- 凭证不进入模型上下文、前端响应、Run 明文快照、日志或 Trace。
- 旧资产提供迁移状态和修复向导；无法推导的字段标记“需补充”，不得自动发布。
- 所有跨模块操作使用公开接口、项目校验、审计和幂等键。

## 11. UI 与可理解性

- 每个字段同时显示“填什么”和“运行时用于什么”，高级字段按需展开。
- 列表显示就绪状态、发布状态、引用数量和最近验证/执行结果。
- 空状态显示前置条件和可执行下一步。
- 所有内部 ID 改为可搜索选择器；详情页仍可复制 ID 用于 API 调试。
- 窄视口收起侧栏，页头操作换到独立行，禁止标题与按钮重叠。
- 导入、连接测试、试评、计划预览和门禁评估都显示结构化错误与恢复建议。

## 12. 验收标准

### 独立模块

- AgentVersion 可完成配置、连接测试、发布和独立对话测试。
- EnvironmentVersion 可保存变量/凭证引用并通过验证，API 永不返回明文。
- 用例文件可下载模板、预检、导入、发布和再次导出；错误精确到行/字段。
- Scorer 可独立试评并产生真实 Score。
- SecurityProfile 可对所选 Agent/环境运行并产生 Finding。
- ReviewTask 可由授权用户完成并保留决定。
- ReleaseGate 可针对真实结果评估并持久化决定。

### 完整链路

- 用户无需输入任何内部 UUID，即可完成资产选择和配置。
- 发布计划后启动 Run，Worker 使用正确 Agent/环境配置执行全部选中用例。
- RunCaseResult 同时包含输出、Trace、断言、评分、成本和安全引用。
- 两个兼容 Run 可形成实验；低置信度或安全问题自动进入审核；门禁读取真实聚合结果。
- 任一执行相关资产可从 Run 反查，任一结果可追踪到版本化输入。
- 超级 Agent 能通过同一能力完成上述链路，不建立第二套事实。
- 模块契约、项目隔离、迁移、Worker 重放、Web 关键流程和完整 E2E 均有自动测试。
