# 超级测试 Agent 与全平台编排设计

## 1. 产品定位

AgentTest 的终态由五个相互连接的能力构成：

1. 对话式测试 Agent：项目级统一意图入口和任务编排中枢。
2. 专业测试控制台：所有业务资产的可编辑、可审计事实源。
3. 自动化执行引擎：通过 Temporal 与独立 Worker 执行 API、浏览器及画布测试。
4. 多维评测引擎：统一规则、模型、视觉、结构和人工评测。
5. 安全红队引擎：生成、执行、分类和闭环安全测试。

超级测试 Agent 不是“计划 JSON 生成器”，而是站在五个能力之上的项目级编排者。它通过受控子 Agent 调用专业模块，不建立独立于控制台之外的第二套数据。

## 2. 现状与需要替换的实现

当前仓库已具备项目级模型配置、Model Runner、消息持久化表、Agent/环境/数据集/测试计划/Run/评分/实验/安全/审核/门禁模块以及 Temporal 执行基础。

当前 Test Agent 实现存在以下结构性缺口：

- 每条用户消息都强制生成一份测试计划 JSON。
- Assistant 文本由控制面固定模板生成，无自然多轮对话。
- 页面不恢复会话、不提供历史列表，也没有流式协议。
- `plan_draft` 是会话 JSON，确认后没有创建真实平台资产。
- 没有子 Agent、工具注册、跨模块任务图、持久化事件或操作确认。
- 没有独立的“被测 Agent 对话测试”会话、Trace 和评分链路。

新架构不保留这条误导性产品路径；现有历史消息可读，但不将旧 `plan_draft` 伪造成业务资产。

## 3. 总体架构

### 3.1 超级 Agent

超级 Agent 拥有一个项目级会话上下文，负责：

- 理解用户目标、识别缺失信息并进行自然追问。
- 将跨模块目标拆成有依赖的任务图。
- 选择子 Agent，决定串行、并行、重试、取消与补偿。
- 对需要用户确认的操作生成可读预览。
- 持续汇总子 Agent 事件、业务资产与执行结果。
- 在会话中解释已做什么、为什么、当前风险和下一步。

超级 Agent 不直接访问 ORM、不持有凭证、不自行越过应用层执行业务写入。

### 3.2 内置子 Agent

| 子 Agent | 责任 | 关键资产/能力 |
|---|---|---|
| 被测智能体 Agent | 选择、校验、创建和发布被测 Agent 版本 | Agent、AgentVersion、协议配置 |
| 环境与凭证 Agent | 选择环境、校验引用、管理受控凭证绑定 | EnvironmentTemplate、TestAccount 引用 |
| 测试数据 Agent | 生成、导入、改写、分类和失败转回归 | Dataset、DatasetVersion、TestCase |
| 测试计划 Agent | 组装执行配置、预算、评分器和门禁阈值 | TestPlan、TestPlanVersion |
| 执行 Agent | 试运行、发布后启动、取消、重试与进度汇总 | Run、RunCase、Trace、Artifact |
| 多维评测 Agent | 选择并配置规则/模型/视觉/结构评分 | Scorer、Score、Evaluation |
| 实验对比 Agent | 选择基线、创建实验、对比版本并解释差异 | Experiment、Comparison |
| 安全红队 Agent | 编排安全策略、执行攻击测试、分类风险并转回归 | SecurityScan、Finding |
| 审核与门禁 Agent | 创建人工审核任务、汇总冲突、评估门禁 | ReviewTask、Decision、ReleaseGate |

首版子 Agent 为内置固定角色，但能力通过注册表装配，后续可在不改超级 Agent 协议的前提下增加子 Agent 或插件能力。

## 4. Capability Registry

每个子 Agent 只能看到自己白名单内的能力。每个能力定义：

- 稳定名称和版本。
- 结构化输入/输出 Schema。
- 所属项目和所需系统/项目权限。
- 风险级别与确认策略。
- 幂等键生成规则。
- 可审计输入摘要和输出资产引用。
- 超时、重试、取消和补偿语义。

能力适配器只调用对应模块的公开 Application Handler 或公开事件，不复制业务规则。专业控制台与 Agent 因此共享同一份领域事实。

## 5. 任务编排与运行时

长任务使用 Temporal Workflow，其中保存可重放的任务图与等待确认状态；外部 I/O 只在 Activity 中完成。

一个编排任务包含：

- 目标、项目、发起用户和会话快照。
- 经校验的步骤及依赖边。
- 子 Agent、Capability、风险级别和确认状态。
- 幂等键、尝试次数、输出资产和错误分类。
- 用于界面恢复的持久化事件序列。

超级 Agent 可并行查询和独立分析，但对有资产依赖的写操作按图串行。工作流不把未完成的后续步骤伪装成成功。

## 6. 对话与流式事件

模型输出分为自然语言内容和结构化操作意图。问候或信息不足时只对话/追问，不无条件生成计划。

SSE 对外事件至少包含：

- `message.started` / `message.delta` / `message.completed`
- `agent.delegated` / `agent.progress` / `agent.completed`
- `tool.preview` / `tool.confirmation_required` / `tool.completed`
- `asset.created` / `asset.updated`
- `run.progress` / `run.completed`
- `error`

事件先持久化再对外发送，每个事件拥有单调 `sequence`。客户端通过 `Last-Event-ID` 续传，刷新、断线或换实例后不丢消息和任务进度。

## 7. 资产与来源链

新增并持久化以下编排事实：

- `test_agent_sessions`：会话元数据、标题、状态和当前上下文。
- `test_agent_messages`：用户、超级 Agent 和子 Agent 消息。
- `test_agent_tasks`：跨模块任务图节点与状态。
- `test_agent_events`：用于 SSE 续传的事件日志。
- `test_agent_confirmations`：风险操作的预览、决策与决策人。
- `test_agent_artifact_links`：会话/任务与平台资产的项目级来源关系。

典型资产链：

`Session -> Task -> DatasetVersion -> TestCase -> TestPlanVersion -> Run -> RunCase/Score/Artifact -> Experiment/SecurityFinding/ReviewTask/ReleaseGateDecision`

每个链接保存 `project_id`、任务、资产类型、资产 ID、关系类型和创建时间。资产可从专业控制台反向定位来源会话，会话也可定位全部下游资产。

## 8. 独立的被测 Agent 对话测试

对话式测试 Agent 是平台编排者；被测 Agent 对话测试是一种真实测试模式，两者不混用。

被测对话测试显式选择 AgentVersion、EnvironmentTemplate 和必要的 TestAccount 引用，调用现有 Agent Adapter 发送真实请求，持久化每轮：

- 输入与原始/规范化输出。
- 响应模式、耗时、Token 和错误分类。
- Trace、工具调用、截图/录像/画布差异。
- 规则、模型、视觉和人工评分。

任意一轮或整段会话可转换为真实 TestCase/DatasetVersion，并保留来源链。

## 9. 权限、确认与安全

超级 Agent 与子 Agent 始终继承发起用户的系统角色和项目成员权限，不存在超级权限。

默认确认策略：

- 自动：查询、分析、推荐、试运行预估。
- 批量确认：创建或修改草稿资产。
- 单独确认：发布版本、启动/取消执行、安全扫描、人工审核决定、门禁策略变更、凭证变更和删除操作。

模型只能看到凭证引用与脱敏提示；明文凭证仅在授权 Worker 的最小边界内解密。任何提示词、被测 Agent 输出和外部内容都不能提升工具权限或改变确认策略。

## 10. 产品交互

沿用现有平台设计 Token 与组件，将 Test Agent 工作区调整为三栏：

- 左栏：项目会话历史、搜索、新建、归档与未完成任务。
- 中栏：流式消息、子 Agent 委派、工具进度、错误和确认卡片。
- 右栏：当前被测 Agent/环境/预算上下文、任务图和关联资产。

页面从 URL 中的会话 ID 恢复，所有重要状态来自 API/SSE，不以 React 内存作为事实源。专业控制台中的资产显示“由 Test Agent 会话生成”的可追溯入口。

## 11. 错误与恢复

- 无默认模型、Worker/Temporal 不可用、供应商失败均明确失败，不产生固定回复。
- 已成功的幂等步骤不重复创建资产；后续步骤可从最后成功点继续。
- 部分失败在任务图和会话中如实展示，并提供有边界的重试/取消操作。
- 跨模块写入使用幂等 Saga，不使用隐式全局事务；已发布的不可变资产不做破坏性补偿。
- 重复模型配置名称映射为稳定 409，不泄露数据库异常。

## 12. 迁移与兼容

- 新迁移只 Expand，保留现有会话与消息记录。
- 旧 `plan_draft` 作为历史消息附件只读展示，不自动创建测试计划。
- 新协议上线后关闭固定模板回复和旧确认路径。
- 会话列表可读取旧会话；只有新会话支持子 Agent 编排和续传。

## 13. 交付分阶段

1. 真实性和会话基础：修复模型配置冲突，替换固定回复，完成会话列表、恢复和项目隔离。
2. 流式事件底座：完成持久化事件、Model Runner 流式回调、SSE 续传和前端增量渲染。
3. 超级 Agent 与 Capability Registry：完成任务图、子 Agent 注册、风险确认和 Temporal 编排。
4. 核心资产闭环：接入被测 Agent、环境、数据集/用例、计划、执行和评分。
5. 高级质量闭环：接入实验对比、安全红队、人工审核和发布门禁。
6. 被测 Agent 对话测试：完成独立会话、Trace、评分与转回归。
7. 端到端收敛：使用真实供应商和真实被测 Agent 验证全链路。

## 14. 验收标准

- “你好”只产生真实流式对话，不自动伪造计划。
- 刷新、重新登录、应用重启和断线续传后，会话、消息和任务状态不丢失。
- 用户能看到超级 Agent 委派子 Agent 以及每步真实状态。
- 从会话创建的 DatasetVersion、TestCase、TestPlanVersion、Run、Score、Experiment、SecurityFinding、ReviewTask 和 GateDecision 均为专业控制台可读可审计的真实资产。
- 专业控制台修改资产后，会话通过领域事件看到最新状态。
- 一个跨模块目标可从需求进入，经用例、计划、执行、评分、实验、安全、审核到门禁结论闭环完成。
- 所有能力强制项目隔离、用户权限、幂等、确认和审计。
- 模型、Temporal、Worker、被测 Agent 或任一下游不可用时明确失败，不生成 Mock、占位或假成功。
