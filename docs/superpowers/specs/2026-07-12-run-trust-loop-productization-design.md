# Run 可信闭环能力产品化设计

## 1. 背景与目标

现有可信闭环已经具备四维 Outcome、不可变 Evidence、确定性故障分类、证据约束诊断、失败回归、评估校准和联合门禁的领域能力，但这些能力尚未形成覆盖普通 Run 与 Mission Run 的统一持久化后处理链路。

本设计将可信闭环产品化为 Run 完成后自动执行的生产能力：结果写入后自动分类、诊断、复现失败、校准评估并计算联合门禁，所有结果按项目隔离持久化，并通过稳定 API 与前端展示。

## 2. 已确认决策

- Run 完成后自动触发可信闭环，不依赖人工操作。
- 模型不可用、超时或额度不足时降级为确定性结果，诊断状态为 `inconclusive`，不阻塞 Run 终态。
- 回归候选仅在最小化后连续两次独立复现、指纹一致时自动发布；不稳定或无法复现的候选进入 Quarantine。
- 采用“持久化任务 + Temporal 后处理工作流”，不在结果回调中同步执行长任务，也不继续扩张 Mission `close_loop`。

## 3. 架构边界

新增 `run_postprocessing` 模块作为后处理编排入口。它只通过公开接口调用 `runs`、`diagnostics`、`regressions`、`scorers` 与 `gates`，不直接读取其他模块 ORM。

Run 结果事务保存业务结果后创建 `RunPostprocessJob`。调度器启动 `RunPostprocessWorkflow`，Workflow 只保存项目 ID、Run ID、管线版本、任务 ID和阶段状态。Worker 不连接业务数据库，所有业务读写均通过带内部认证的 Control API 端点完成。

普通 Run 与 Mission Run 使用同一条后处理管线。Mission 只消费后处理摘要，不维护第二套诊断、回归或门禁逻辑。

固定阶段如下：

```text
classify -> diagnose -> reproduce -> calibrate -> evaluate_gate -> finalize
```

每个阶段拥有独立幂等键、状态、重试策略和可审计输出。后续管线升级通过不可变 `pipeline_version` 区分，不改写历史结论。

## 4. 数据模型

### 4.1 RunPostprocessJob

- `id`, `project_id`, `run_id`, `pipeline_version`
- `status`: `pending | running | completed | completed_with_warnings | failed`
- `current_stage`, `workflow_id`, `attempt`
- `warning_codes`, `error_type`, `error_message`
- `created_at`, `started_at`, `completed_at`, `updated_at`
- 唯一约束：`(project_id, run_id, pipeline_version)`

### 4.2 DiagnosticRecord

- 关联 `project_id`, `run_id`, `run_case_id`
- 保存状态、确定性分类、置信度、Evidence 引用、反证、验证步骤和模型适配器版本
- 只允许引用同项目、同 Run Case、完整性校验通过且已脱敏的 Evidence
- 模型失败写入 `inconclusive`，不得伪造诊断文本

### 4.3 RegressionCandidateRecord

- 保存失败指纹、原始输入引用、最小化输入、复现次数、状态和目标数据集版本
- 状态：`draft | reproducing | verified | published | quarantined`
- 两次复现必须使用独立 Run Case 执行记录；环境故障、平台故障和评估故障不自动发布为产品回归用例

### 4.4 CalibrationRecord 与 JointGateDecision

- 校准记录保存样本集版本、指标、冲突仲裁结果和评估器版本
- 联合门禁保存基线 Run、当前 Run、每条规则、输入事实、判定和解释
- 安全失败、Evidence 不完整、执行失败均不可被质量分补偿

所有表强制包含 `project_id`，复合外键、唯一约束和核心查询索引均包含项目作用域。

## 5. 执行流程

1. Run 结果处理器验证回调、Evidence 和 Outcome，并保存 Run 终态。
2. 同一应用事务创建或取得唯一后处理任务；重复回调不会创建第二个任务。
3. 提交后调度器以稳定 Workflow ID 启动 Temporal Workflow；调度失败保留 `pending`，由补偿扫描器恢复。
4. `classify` 对每个失败 Case 运行确定性分类并持久化。
5. `diagnose` 只向模型提供允许字段和 Evidence 引用；失败降级为 `inconclusive`。
6. `reproduce` 仅处理可回归的目标/测试失败，执行有预算上限的最小化和两次独立复现。
7. `calibrate` 计算评估一致性、冲突和可用性；样本不足时记录不可判定。
8. `evaluate_gate` 使用不可补偿的有序规则比较基线和当前 Run。
9. `finalize` 生成稳定摘要，将任务标记为 `completed` 或 `completed_with_warnings`。
10. Mission 等待摘要后完成自己的资产关联；普通 Run 可直接读取相同摘要。

## 6. API 与前端

对外 API：

- `GET /projects/{project_id}/runs/{run_id}/trust-loop`
- `GET /projects/{project_id}/runs/{run_id}/diagnostics`
- `GET /projects/{project_id}/runs/{run_id}/regressions`
- `GET /projects/{project_id}/runs/{run_id}/calibration`
- `GET /projects/{project_id}/runs/{run_id}/joint-gate`

内部 API：

- 创建/认领任务、执行单阶段、完成任务和查询任务状态
- 所有请求要求内部 Token、项目 ID、Run ID、管线版本和幂等键

Run 详情页展示阶段进度、四维 Outcome、Evidence 完整性、故障分类、诊断引用、回归状态、校准和门禁解释。模型降级、样本不足和 Quarantine 使用明确状态，不显示为成功。测试 Agent 复用同一生成客户端契约。

## 7. 失败、重试与恢复

- 确定性分类、持久化和门禁属于必需阶段；耗尽重试后任务为 `failed`，但不回滚已完成 Run。
- 模型诊断、回归复现和校准属于可降级阶段；失败产生警告并继续后续阶段。
- Activity 使用有界指数退避；目标产品错误不进行平台级无限重试。
- Workflow replay 不读取时间、随机数、环境变量或网络。
- 重复回调、重复 Workflow 启动、Worker 重启和滚动版本混部都必须保持幂等。
- 补偿扫描器只重启超时的 `pending/running` 任务，并使用相同 Workflow ID 和管线版本。

## 8. 安全与审计

- 模型输入使用 Evidence 脱敏投影，不包含凭证、Cookie、Token、原始 HTML 或非允许字段。
- 模型不能修改 Evidence、Outcome、故障分类或发布门禁，只能提出带引用的诊断候选。
- 回归输入发布前再次执行秘密扫描和项目作用域校验。
- 自动发布只对允许的失败类别生效，且必须满足两次复现和动作 Allowlist。
- 每个阶段记录审计事件、输入版本、输出摘要和失败原因；日志只记录 ID 和脱敏元数据。

## 9. 测试与验收

### 领域与应用测试

- 后处理状态机、唯一任务和每阶段幂等
- Evidence 引用越权、跨项目和完整性失败
- 模型不可用降级为 `inconclusive`
- 两次复现发布、一次复现不发布、波动结果进入 Quarantine
- 安全/执行/Evidence 失败不可被质量分补偿

### 集成测试

- PostgreSQL 空库迁移、上一版升级、复合外键、唯一约束、索引和项目隔离
- Run 结果与后处理任务一致性、重复回调、调度失败补偿
- Control API 内部端点认证、OpenAPI 和生成客户端

### Workflow 与全链路测试

- Temporal replay、Activity 重试、超时、取消、Worker 重启和版本混部
- Fake Target 成功、目标错误、协议错误、认证、限流、超时、瞬态和安全失败矩阵
- 公共路径验证 Run、诊断、回归候选、校准和联合门禁均有真实持久化结果

### 前端验证

- format、lint、typecheck、组件测试、关键 Playwright、生产构建
- 加载、处理中、完成、警告、失败、无结论和 Quarantine 状态均可访问且不发生布局偏移

## 10. 非目标

- 不让模型直接决定发布或修改原始测试事实。
- 不在本轮引入新的外部可观测平台或评估框架。
- 不为缺少专用账号、登录态或额度的真实目标伪造验收证据。
- 不把普通 Run 强制包装成 Test Mission。
