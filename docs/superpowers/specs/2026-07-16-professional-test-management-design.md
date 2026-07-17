# 专业测试资产、全量核心列表与 Agent 闭环统一设计

- 日期：2026-07-16
- 状态：已批准，待实施计划
- 任务：TASK-20260716-001
- 范围：项目、Agent、数据集、测试用例、测试计划、运行、环境、评分器、实验、安全扫描、人工审核、发布门禁、Test Agent 和 Worker

## 1. 背景

平台已经具备测试资产、版本、运行、评估、安全和门禁模块，但当前体验存在三个结构性问题：

1. 测试用例虽然有输入、断言、评分和安全字段，却缺少测试工程师日常使用的测试目标、前置条件、标准步骤、逐步测试数据与预期结果、后置条件、负责人、需求追踪和自动化状态。
2. 手工表单、导入导出、Test Agent 生成和 Worker 执行分别理解自己的字段子集，AI 生成内容可以入库但不一定形成专业、可评审、可直接执行的资产。
3. 核心列表多为名称、状态、更新时间和操作，缺少版本、关联资源、覆盖、执行结果、成本和风险等决策字段；Test Agent 虽能调用多数模块，返回的资源摘要和跨模块引用仍过于简单。

本设计不是只增加表格列。它建立唯一的专业测试用例契约，并让人工编辑、AI 生成、导入导出、计划编排、单用例试运行、批量运行和结果分析共同消费该契约。

## 2. 设计依据

产品和架构依据：

- PRD 5.5：Agent 生成的计划、用例和评分器必须成为可编辑、可复用、可审计的结构化资产。
- PRD 6.6：对话式 Test Agent 与结构化控制台双向同步。
- PRD 6.7：列表支持筛选、排序、分页、列显隐、详情和保存视图。
- PRD 8：Agent、数据集、用例、计划、运行和质量安全资产的字段与版本要求。
- ADR-0004：所有数据访问强制项目隔离。
- ADR-0007：已发布资产不可变，编辑通过新草稿版本完成。

市场格式参考：

- TestRail 用例字段：https://support.testrail.com/hc/en-us/articles/14940939006740-Test-case-fields
- TestRail 用例模板：https://support.testrail.com/hc/en-us/articles/14927678348052-Test-case-templates
- Zephyr Scale API：https://support.smartbear.com/zephyr-scale-cloud/api-docs/
- Zephyr 步骤参数：https://support.smartbear.com/zephyr-scale-cloud/docs/en/test-cases/parameters.html
- Qase 用例格式：https://docs.qase.io/en/articles/5563704-test-cases

这些产品共同使用可读编号、目标或摘要、前置条件、操作步骤、测试数据、预期结果、优先级、负责人、需求引用、估时和自动化属性。本设计在此基础上增加 Agent 测试所需的机器断言、AI 评分器、安全策略、证据要求和执行模式。

## 3. 目标

### 3.1 产品目标

- 测试工程师可以完全通过平台表单新增、复制、编辑、校验、发布和试运行专业测试用例。
- Test Agent 生成的用例与人工表单使用完全相同的 PlatformTestCaseV1 契约。
- 用例可直接进入计划或单独试运行，执行结果能回到用例、Agent、计划、实验、审核和门禁。
- 全部核心列表展示足以做判断的默认字段，并能导航到关联资产。
- 旧数据和旧 API 客户端可以渐进迁移，不丢失现有输入、断言或执行能力。

### 3.2 工程目标

- 可检索、可排序字段使用关系型列；复杂但受约束的结构使用经过 Schema 校验的 JSONB。
- 聚合列表使用专用查询 DTO 和集合查询，禁止逐行 N+1 查询。
- Worker 只消费 Control API 生成的不可变、无秘密快照，不连接业务数据库。
- 所有创建、更新、发布和执行路径共享领域不变量、权限检查和审计。

## 4. 非目标

- 本任务不实现管理员可视化配置任意字段类型的动态字段设计器。
- 本任务不复制某个市场产品的完整工作流或文件夹体系。
- 本任务不把真实凭证值保存到用例、计划、运行快照或 Agent 消息。
- 本任务不改变已发布资产不可变原则。
- 本任务不替代现有插件 SDK，而是把标准契约通过公开接口提供给插件。

## 5. 方案选择

采用兼容优先的强类型核心契约加受限扩展字段方案。

未采用纯 JSONB 方案，因为它无法保证人工、Agent、导入和执行对字段具有相同解释，也无法稳定支持筛选和统计。

未采用完整动态字段引擎，因为字段设计器、模板管理、索引策略、迁移规则和权限模型会显著扩大本次范围，且不是当前专业测试闭环的必要前提。

## 6. 项目专业字段

Project 增加并公开：

- key：全局唯一、创建后不可变的可读项目编码。
- description：项目目标、范围和说明。
- lead_user_id：项目负责人，必须是当前项目成员或创建人。
- status：由 active 和 archived 两种状态组成，继续以归档时间作为事实源。
- created_by、updated_by、created_at、updated_at。

项目 key 规则：

- 格式为 2 到 12 位大写字母、数字或连字符，第一位必须是字母。
- 新建表单可以输入；未输入时后端根据名称生成，并加入项目 UUID 的稳定短后缀避免并发冲突。
- 数据库唯一约束是最终一致性边界。
- key 在创建后不可修改，避免已有用例编号和外部引用失效。
- 旧项目以 P 加项目 UUID 前八位的确定性形式回填。

ProjectSummary 查询 DTO 额外包含：

- member_count、agent_count、dataset_count、test_case_count、test_plan_count。
- last_run_id、last_run_status、last_run_at。
- active_environment_count 和 open_review_count。

统计必须在项目范围内通过集合聚合查询完成，不调用各模块列表接口逐项累加。

## 7. PlatformTestCaseV1

### 7.1 身份与治理字段

- case_key：项目 key 加 TC 加六位序号，例如 DEMO-TC-000012。
- name：用例标题，1 到 500 字符。
- objective：测试目标，必须描述要验证的行为。
- case_status：draft、ready 或 deprecated。
- template：step_by_step、text、bdd 或 ai_eval。
- case_type：functional、regression、smoke、integration、e2e、security、performance、usability 或 exploratory。
- automation_status：manual、candidate 或 automated。
- source：manual、agent_generated、imported 或 run_regression。
- source_ref：可选的 Agent generation、Run 或导入批次引用。
- component：所属产品模块或组件。
- requirement_refs：最多 50 个需求、Issue 或外部测试管理引用。
- owner_id：可选负责人，必须是项目成员。
- priority、risk_level、difficulty、tags 和 test_group：保留现有分类能力。
- created_by、updated_by、created_at、updated_at。

用例生命周期由 case_status 表示用例是否可用于正式计划；数据集版本状态表示整个快照是否已发布。二者含义不同：

- 新建和 AI 生成默认 draft。
- 校验全部通过后可标记 ready。
- deprecated 用例保留历史但默认不进入新计划。
- 发布数据集版本时，所有被选入正式执行的用例必须为 ready。

### 7.2 测试准备字段

- preconditions：有序非空字符串列表，描述身份、数据、系统或环境前置条件。
- initial_state：保留现有结构化初始业务状态。
- input：运行时输入数据对象，是 API 请求或浏览器交互中的参数事实源。
- data_bindings：测试数据来源列表，每项包含 name、source、value 或 reference、value_type、sensitive 和 description。

data_bindings 的 source 支持：

- literal：非敏感固定值。
- environment：环境配置引用。
- credential：凭证绑定引用。
- fixture：数据夹具引用。
- generated：运行前按规则生成。

sensitive 为 true 时禁止保存 value，只允许 reference。API、审计、Agent 消息、日志、Trace 和 Artifact 均不得返回秘密值。

### 7.3 标准操作步骤

steps 是有序 TestStepV1 列表。每一步包含：

- step_no：从 1 开始且连续，保存时由服务端规范化。
- action：测试人员或执行 Agent 要完成的明确动作。
- test_data：本步骤使用的数据对象，可通过模板引用顶层 input 和 data_bindings。
- expected_result：人工可读的预期结果。
- assertions：作用于本步骤的机器断言列表。
- artifact_requirements：本步骤必须采集的响应、截图、Trace、画布快照或文件要求。

step_by_step 模板至少需要一个步骤，且每步 action 和 expected_result 必填。

text 模板可以没有固定步骤，但必须有 objective、input 和 expected_outcome。

bdd 模板使用 structured BDD 内容，仍编译为相同的 preconditions、steps 和 expected_outcome。

ai_eval 模板允许步骤较少，但必须提供 objective、input、expected_outcome 和至少一个机器断言或评分器。

### 7.4 验证与收尾字段

- expected_outcome：结构化整体预期。
- assertions：用例级确定性断言。
- scorers：AI 或规则评分器及阈值。
- security_policies：越权、隐私、提示注入、工具使用等安全约束。
- artifact_requirements：用例级证据要求。
- postconditions：测试后的数据清理和状态恢复要求。
- estimated_duration_seconds：1 到 86400 秒。
- execution_mode：api、browser 或 codex_explore。
- timeout_seconds 和 retry_count：用例级覆盖值，未设置时使用计划默认值。
- custom_fields：最大 16 KiB 的 JSON 对象，键和值受 Schema、深度和敏感信息规则限制。

### 7.5 唯一契约实现

Datasets 模块公开 PlatformTestCaseV1、TestStepV1、DataBindingV1 和 ArtifactRequirementV1 应用契约。

以下路径必须从该公开契约构造领域命令：

- 人工表单新增和编辑。
- JSON、JSONL 和 CSV 导入。
- Test Agent create_with_cases。
- Test Agent auto_generate_cases。
- 失败运行生成回归用例。
- 复制用例和新版本复制。
- API、Browser 和 Codex Explore 执行快照编译。

禁止各路径维护字段不一致的临时字典转换函数。API Schema、Agent JSON Schema 和生成客户端由同一应用契约映射并通过契约测试锁定。

## 8. 持久化与迁移

### 8.1 项目

projects 增加：

- key，非空唯一。
- lead_user_id，可空用户外键。

现有 description、created_at、updated_at、created_by 和 updated_by 纳入领域映射和 API，不再只存在于 ORM。

### 8.2 用例

test_cases 增加：

- case_key、objective、case_status、template、case_type、automation_status、source、source_ref。
- component、requirement_refs、owner_id。
- preconditions、data_bindings、steps、artifact_requirements、postconditions。
- estimated_duration_seconds、timeout_seconds、retry_count、custom_fields。
- created_by、updated_by。

保留现有 input、initial_state、expected_outcome、assertions、scorers、security_policies、tags、scenario、priority、risk_level、difficulty、test_group 和 sort_order。

可筛选枚举字段使用列和 Check Constraint。结构字段使用 JSONB，并在应用层执行强 Schema 校验；数据库确保非空、范围、外键和唯一性。

### 8.3 编号分配

新增 project_sequences：

- project_id。
- resource_type。
- next_value。
- project_id 和 resource_type 唯一。

基础设施通过单条原子 upsert returning 分配序号，禁止查询 max 再加一。CaseKeyAllocatorPort 只暴露项目范围内的下一编号，不向领域泄露 SQL。

### 8.4 回填

- 旧项目先确定性回填 key。
- 旧用例按项目、数据集、版本、sort_order 和 id 的稳定顺序回填 case_key。
- objective 回填为现有 scenario；scenario 为空时使用 name。
- case_status 回填 ready。
- template 根据 execution_mode 和现有字段回填 ai_eval 或 step_by_step；没有步骤的旧用例仍合法。
- automation_status 回填 automated。
- source 回填 manual。
- preconditions、data_bindings、steps、artifact_requirements、postconditions 和 custom_fields 回填空结构。
- created_by 和 updated_by 回填所属 DatasetVersion 创建人。
- project_sequences 更新到每个项目已分配的最大编号之后。

迁移必须同时支持空数据库和上一版本数据库升级。Downgrade 只删除新增派生字段和表，不改写旧 input、assertions 或运行记录。

## 9. API 设计

### 9.1 项目 API

创建和更新项目支持 description 与 lead_user_id；创建支持可选 key。

项目列表和详情返回 ProjectSummary。旧的 id、name 和 archived 字段继续保留。

### 9.2 用例 API

创建、更新、列表和详情使用 PlatformTestCaseV1。

新增动作：

- validate：返回字段级错误、警告和 readiness。
- mark-ready：只有编辑者可调用，失败时返回完整校验问题。
- duplicate：在同一草稿版本复制并分配新 case_key。
- trial-run：选择不可变 Agent 版本和环境后创建单用例试运行。

列表支持：

- case_key、name、component、case_type、case_status、automation_status。
- priority、risk_level、owner_id、execution_mode、source、tag。
- 最近执行状态、更新时间、全文搜索。

导入预览必须显示字段映射、默认值、未知字段、逐行错误和敏感数据拒绝。导出 JSON 与 JSONL 使用完整 V1；CSV 使用扁平基本字段和 JSON 编码的复杂字段。

### 9.3 兼容

现有 input、assertions 等字段保持可读写。新增请求字段在过渡期可选，服务端应用明确默认值。

响应只提供一个事实源，不同时保存 input 和 input_data 两份可漂移数据。前端标签显示“输入数据”，API 字段继续使用 input。

OpenAPI 生成客户端必须在同一提交中更新，api-check 不允许漂移。

## 10. 单用例试运行

runs 增加 run_type：

- plan：现有计划运行。
- case_trial：从用例表单发起的单用例试运行。

case_trial 可以没有 test_plan_version_id，但必须有 source_test_case_id、AgentVersion、Environment 和一个不可变 RunCase 快照。

创建试运行时 Control API：

1. 校验项目权限、目标 Agent 版本、环境和凭证引用同项目。
2. 对当前草稿执行 PlatformTestCaseV1 校验。
3. 编译并持久化完整、无秘密的 case_spec_snapshot。
4. 创建审计记录和幂等运行。
5. 通过现有 Temporal/Worker 公开协议调度。

Worker 不读取 TestCase 表。API、Browser 和 Codex Explore Runner 从同一个 case_spec_snapshot 获取 objective、input、steps、assertions、scorers、安全策略和证据要求。

试运行结果通过 source_test_case_id 聚合回用例详情，展示最近状态、耗时、评分、失败原因、截图、Trace 和 Artifact。正式质量统计默认排除 trial，除非查询显式包含。

## 11. 核心列表读模型

每个列表使用 Application Query Handler 和公开 Summary DTO。Repository 提供项目过滤的集合查询和聚合查询。API 不直接使用 ORM。

### 11.1 项目

默认列：

- key、name、lead、status、member_count。
- agent_count、test_case_count、test_plan_count。
- last_run_status、last_run_at、updated_at。

### 11.2 Agent

默认列：

- name、agent_type、current_version、version_status。
- protocol、model、tool_count、credential_binding_count。
- connection_status、last_run_status、pass_rate、updated_at。

### 11.3 数据集

默认列：

- name、latest_version、version_status、case_count。
- ready_count、api_count、browser_count、codex_explore_count。
- priority_coverage、source_distribution、published_at、updated_at。

### 11.4 测试用例

默认列：

- case_key、name、component、case_type、case_status。
- priority、risk_level、automation_status、execution_mode、owner。
- last_run_status、updated_at。

### 11.5 测试计划

默认列：

- name、version、version_status。
- agent_ref、dataset_ref、environment_ref、case_count。
- repeat_count、concurrency、timeout、retry、scorer_count。
- last_run_status、pass_rate、updated_at。

### 11.6 测试运行

默认列：

- run_number、run_type、plan_ref、agent_ref、dataset_ref。
- trigger_type、status、progress。
- passed、failed、error、cancelled。
- duration、token_usage、cost、created_by、created_at。

### 11.7 环境

默认列：

- name、template_type、current_version、status。
- credential_binding_count、browser_profile_ref。
- validation_status、last_validated_at、last_run_at、updated_at。

### 11.8 评分器

默认列：

- name、scorer_type、version、weight、threshold。
- status、usage_count、last_calibrated_at、updated_at。

### 11.9 实验

默认列：

- name、baseline_run_ref、candidate_run_ref、status。
- case_count、improved_count、regressed_count。
- pass_rate_delta、score_delta、cost_delta、updated_at。

### 11.10 安全扫描

默认列：

- agent_ref、run_ref、profile_ref、scan_type、status。
- critical_count、high_count、medium_count、low_count。
- duration、started_at、completed_at。

### 11.11 人工审核

默认列：

- run_ref、case_ref、enqueue_reason、confidence。
- priority、assignee、status、age、updated_at。

### 11.12 发布门禁

默认列：

- name、scope、enabled、rule_summary。
- last_decision、blocking_count、last_run_ref、evaluated_at。

### 11.13 统一列表规则

- 默认列在 1280 像素宽度可完成主要判断；非默认列通过列显隐和详情抽屉访问。
- 移动端使用现有同一 DOM 的纵向字段布局，不能丢失状态和主操作。
- 筛选、排序和分页在服务端执行并同步 URL。
- 关联资源均返回 ResourceReference，禁止前端根据 ID 猜测名称或版本。
- 聚合统计必须有 SQL 查询预算测试。

## 12. ResourceReference

跨模块统一引用包含：

- resource_type。
- id。
- key，可选。
- name。
- version，可选。
- status，可选。
- href。

href 由服务端认可的资源类型和 ID 生成或由前端路由映射生成，不接受模型提供任意 URL。

运行、实验、安全扫描、审核和门禁返回关联引用。列表和 Test Agent 产物卡直接使用引用跳转到详情，避免用户手工复制 UUID。

## 13. 平台表单

测试用例编辑器使用单个受控表单，分为：

1. 基本信息。
2. 测试准备。
3. 输入数据。
4. 操作步骤。
5. 断言、评分与安全。
6. 收尾与执行设置。
7. 高级标准 JSON。

### 13.1 基本交互

- 所有字段提供中文标签、说明、示例、必填状态和行内错误。
- 输入数据使用键值表格，支持值类型、来源和敏感标记。
- 前置和后置条件支持逐项新增、删除和排序。
- 操作步骤支持新增、复制、删除和拖动排序。
- 每个步骤分别编辑 action、test_data、expected_result、assertions 和 artifact_requirements。
- JSON 高级视图与表单双向映射，但只能提交通过 V1 Schema 的内容。
- 页面离开前提示未保存修改。

### 13.2 人工与 AI 协作

- 人工新增、AI 生成和导入都进入同一个草稿表单。
- AI 可以补全目标、前置条件、输入、步骤、断言或评分器。
- AI 修改先展示字段级差异，用户接受后才写入。
- AI 不得自动把 draft 标记为 ready 或发布数据集。
- 表单展示 source 和 source_ref，保留生成来源。

### 13.3 版本和动作

- 草稿版本可保存、校验、复制、试运行和加入计划。
- 已发布版本只读；编辑动作创建新草稿版本。
- 保存并试运行必须选择 Agent 版本与环境，并在外部写操作风险存在时显示确认。
- 用例列表支持批量修改分类字段，但不批量覆盖输入、步骤、断言或敏感引用。

## 14. Test Agent 能力闭环

Test Agent 增加并统一以下能力：

- projects.get。
- agents.list 和 agents.get。
- environments.list 和 environments.get。
- datasets.list、datasets.get、datasets.create、datasets.create_version 和 datasets.publish_version。
- test_cases.list、test_cases.get、test_cases.create、test_cases.update、test_cases.validate、test_cases.mark_ready 和 test_cases.trial_run。
- test_plans.list、test_plans.get、test_plans.create_version 和 test_plans.publish_version。
- runs.list、runs.get_status、runs.start 和 runs.cancel。
- scorers、experiments、security_scans、reviews、release_gates 和 reports 的现有读写能力及详情查询。

能力输入：

- test_cases.create 和 update 直接使用 PlatformTestCaseV1 的输入 Schema。
- auto_generate_cases 要求模型返回完整 V1 cases 数组。
- 模型输出先经严格 JSON 解析、Schema 校验、项目引用解析和敏感值检查，再进入领域命令。
- 非法枚举、缺失必填步骤、秘密明文、跨项目引用和未知大字段返回结构化错误，不静默丢弃。

能力输出：

- 所有资源返回 ResourceReference。
- 列表返回与控制台一致的 Summary DTO，而不是只有 id、name 和 status。
- 创建和更新返回 changed_fields、validation 和 artifacts。
- 运行状态返回关联用例 key、快照摘要、执行结果和证据引用。

风险边界：

- 查询、校验和端点分析为 READ。
- 创建或更新草稿为 DRAFT_WRITE。
- 发布、试运行、正式运行、安全扫描、审核入队和门禁评估为 HIGH_IMPACT。
- HIGH_IMPACT 继续要求确认、幂等键、权限和审计。

## 15. 执行编译

PlatformTestCaseV1 根据 execution_mode 编译：

### 15.1 API

- input 进入 AgentVersion 的请求模板。
- steps 作为可审计的测试意图和多步 API 编排输入；单步兼容现有请求路径。
- assertions 对响应执行确定性验证。
- scorers 对输出执行语义或模型评估。

### 15.2 Browser

- preconditions 和 data_bindings 准备浏览器身份与环境。
- steps 驱动 Browser Harness。
- 每步 expected_result 和 assertions 在步骤边界验证。
- artifact_requirements 决定截图、DOM 摘要、网络响应和 Trace 采集。

### 15.3 Codex Explore

- objective、preconditions、input、steps 和 safety_scope 组成受控探索任务。
- 固定步骤存在时必须遵守；没有固定步骤时只能在 objective 和安全边界内规划。
- 模型输出不能扩大允许动作范围。
- expected_outcome、assertions、scorers 和 security_policies 决定结论。

postconditions 只执行明确允许的清理动作。高风险清理不得由模型自行推断。

## 16. 安全与隔离

- 所有列表、详情、导出、复制、试运行和 Agent 能力显式接收并校验 project_id。
- owner、lead、AgentVersion、Environment、Scorer、Credential 和 BrowserProfile 引用必须属于同一项目。
- API 层不直接访问 ORM。
- Worker 不直接连接业务数据库。
- credential data binding 只携带绑定 ID，Worker 在 Activity 内按现有短期租约取密。
- 自定义字段限制大小、深度、键数量和危险键名。
- HTML、Markdown、URL、模型输出、导入文件和 Artifact 名称均按不可信输入处理。
- 审计记录资源 key 和变更字段，不记录秘密值。

## 17. 性能与可维护性

- Summary DTO 与 Detail DTO 分离，列表不传输完整 steps、assertions、Trace 或 Artifact。
- 统计通过子查询、窗口函数或分组查询批量完成。
- 项目列表、项目内核心列表和用例列表建立与 project_id、状态、更新时间、case_key 相匹配的索引。
- API 查询预算测试锁定主要列表的最大 SQL 次数。
- 前端按 Feature 组织，列表列定义、详情抽屉和表单从各自 Feature 的公开出口暴露。
- Test Agent 只依赖各业务模块 public，不依赖 Infrastructure。
- PlatformTestCaseV1 的契约转换集中在 Datasets Application，不在各适配器复制。

## 18. 错误处理

- 表单校验返回 field、code、message 和 severity。
- 批量导入返回行号、字段路径、错误代码和预览，不部分写入。
- AI 输出校验失败保留生成结果和错误摘要，允许重新生成，不创建半成品用例。
- 试运行创建失败不留下可见的空 Run。
- Worker 不支持的步骤类型返回明确 protocol_error，不默默跳过。
- 聚合统计不可用时返回可识别的降级字段，不伪造零值。

## 19. 测试策略

### 19.1 TDD 顺序

1. 先锁定 PlatformTestCaseV1 领域和应用不变量。
2. 再实现迁移和仓储映射。
3. 再实现 API、导入导出、Agent 生成和执行快照。
4. 再实现 Summary DTO 与所有核心列表。
5. 最后实现表单、试运行交互和跨资源导航。

### 19.2 后端

- 领域测试：枚举、步骤连续性、模板必填、敏感数据、ready 转换。
- 迁移测试：空库、上一版本升级、回填、序号并发唯一性、约束和索引。
- 项目隔离：所有新增查询、详情、引用、导出和试运行拒绝跨项目。
- 不可变性：发布版本不能编辑、复制或被 AI 覆写。
- 契约测试：OpenAPI、导入导出、Test Agent Schema 和生成客户端一致。
- 查询预算：每个核心列表无 N+1。

### 19.3 Worker

- 三种执行模式消费相同 case_spec_snapshot。
- 步骤顺序、输入模板、断言、评分、安全和 Artifact 要求正确传递。
- timeout、retry、cancel、idempotency 和 postcondition 失败分类。
- 快照和 Workflow History 不包含秘密。

### 19.4 前端

- 人工完整新增和编辑。
- 输入数据、前置条件、步骤、逐步预期、断言和后置条件数组操作。
- AI 差异接受和拒绝。
- 发布只读和新草稿编辑。
- 单用例试运行选择、确认、进度和结果。
- 全部核心列表默认列、筛选、排序、列显隐、详情和关联跳转。
- 1280、1440、1920 和 390 像素无横向溢出和操作遮挡。
- 键盘导航、标签、错误关联和焦点顺序。

### 19.5 全量门禁

- format、lint、typecheck。
- Python 单元、集成、契约、架构和 PostgreSQL 测试。
- Web unit/component、关键 Playwright E2E 和 production build。
- OpenAPI 与生成客户端漂移检查。
- make performance、make security-audit 和 make verify。

## 20. 验收标准

1. 测试工程师可在平台表单新增包含输入数据、前置条件、标准操作步骤、逐步预期结果、断言和后置条件的完整用例。
2. AI 生成的用例通过同一表单打开、编辑、校验和保存，字段不丢失。
3. 手工、导入、Agent 和失败回归四种来源使用同一 PlatformTestCaseV1。
4. API、Browser 和 Codex Explore 都从不可变 V1 快照执行。
5. 单用例可以从表单试运行并回显结果和证据。
6. 已发布数据集版本不可修改，编辑创建草稿。
7. 全部核心模块列表展示本设计定义的默认决策字段，并能跳转到关联资源。
8. Test Agent 能查询、创建、更新、校验、发布、执行和分析相关资产，所有操作受权限、项目隔离、确认和审计约束。
9. 旧项目和旧用例迁移后仍可查看、导出和执行。
10. 关键列表没有 N+1，全部质量、安全、架构和构建门禁通过。

## 21. 发布与回滚

采用 Expand、Migrate、Contract：

1. Expand：增加可空列、约束准备和序列表。
2. Migrate：确定性回填项目 key、用例 key、专业字段和序号。
3. Enforce：应用切换到 V1 后将必需字段改为非空并启用完整约束。
4. Contract：仅在兼容窗口结束后移除废弃输入别名；本任务不删除现有字段。

前端在 API 与生成客户端发布后切换。Worker 在控制面能够同时生成旧快照和 V1 快照的兼容窗口内升级。

如果发布失败：

- 停用新表单动作和 case_trial 入口。
- 继续使用现有 input、assertions 和计划运行路径。
- 新增列不会改变旧字段语义。
- 回滚前确认没有依赖 V1 专有步骤的待执行 Run。

## 22. 已批准决策

- 覆盖全部核心模块，不只项目和用例。
- 采用兼容优先的强类型核心契约加受限 custom_fields。
- 用例采用专业测试工程师格式，明确输入数据、操作步骤、测试数据和预期结果。
- 平台提供完整人工新增、编辑和校验表单。
- AI 生成和人工表单使用同一格式。
- 支持从用例表单发起单用例试运行。
- 已发布版本保持不可变。
- 不实现动态字段设计器。
