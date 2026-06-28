# PRD 全量功能迭代计划

> **按 PRD 章节顺序逐章推进，每章完成后验收再进入下一章。**
> 前端按方案 1 设计规范打磨，不接受"大概样子"。

**总览：**

| 阶段 | PRD 章节 | 目标 | 状态 |
|---|---|---|---|
| 一 | 8.2 | Agent 与版本管理深化 | ✅ 已完成 |
| 二 | 8.3 | 测试数据集与用例增强 | ✅ 已完成 |
| 三 | 8.4 | 测试环境管理 | ✅ 已完成 |
| 四 | 8.5 | 测试计划增强 | ✅ 已完成 |
| 五 | 8.8 | Trace 与可观测性 | ✅ 已完成 |
| 六 | 8.9 | 断言与评分器管理 | ✅ 已完成 |
| 七 | 8.10 | 实验与版本对比 | 待开始 |
| 八 | 8.11 | 人工审核 | 待开始 |
| 九 | 9.1 | 安全测试 | 待开始 |
| 十 | 8.12 | 发布门禁 | 待开始 |
| 十一 | 6.6 | 测试 Agent 对话入口 | 待开始 |

---

## 阶段一：Agent 与版本管理深化（PRD 8.2）

**目标：** Agent 详情页完整化，支持版本生命周期管理。

**范围：**
- `apps/control-api/src/agenttest/modules/agents/`：版本字段扩展、版本对比 API
- `apps/web/src/features/agents/`：详情页 tabs、版本列表、对比视图

### 后端任务

#### 1.1 Agent 版本字段扩展

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/agents/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/infrastructure/persistence/models.py`
- Create: `apps/control-api/migrations/versions/0006_agent_version_fields.py`

- [ ] `AgentVersion` 新增字段：
  - `model_name`: str — 使用的模型名称
  - `model_params`: JSON — 模型参数（temperature、top_p 等）
  - `system_prompt_version`: str — System Prompt 版本标识
  - `tools_schema`: JSON — 工具清单及 Schema
  - `knowledge_version`: str — 知识库或数据版本
  - `max_steps`: int — 最大执行步骤数（默认 20）
  - `timeout_seconds`: int — 超时秒数（默认 300）
  - `cost_limit`: float | null — 成本限制（单位：分）
  - `adapter_version`: str — AgentAdapter 版本
- [ ] 迁移 0006：ALTER TABLE 新增以上字段，全部带默认值（向后兼容）
- [ ] 更新 `CreateAgentVersionHandler` 支持新字段入参
- [ ] 更新 `UpdateAgentVersionHandler` 支持新字段编辑

#### 1.2 版本对比 API

**Files:**
- Create: `apps/control-api/src/agenttest/modules/agents/api/version_diff.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/api/router.py`

- [ ] `GET /api/v1/projects/{project_id}/agents/{agent_id}/versions/{v1_id}/diff/{v2_id}` 
- [ ] 返回逐字段 diff 结果：`{ field, left_value, right_value, changed: bool }`
- [ ] 支持嵌套 JSON 字段（tools_schema、model_params）深度对比

#### 1.3 版本基线标记

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/agents/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/api/router.py`

- [ ] Agent 实体新增 `current_version_id` + `baseline_version_id` 字段
- [ ] `PATCH /api/v1/projects/{project_id}/agents/{agent_id}/current-version` 设置当前版本
- [ ] `PATCH /api/v1/projects/{project_id}/agents/{agent_id}/baseline-version` 设置基线版本
- [ ] 发布新版本时自动更新 `current_version_id`

### 前端任务

#### 1.4 Agent 详情页重构

**Files:**
- Modify: `apps/web/src/app/(platform)/projects/[projectId]/agents/[agentId]/page.tsx`
- Create: `apps/web/src/features/agents/agent-detail-screen.tsx`
- Create: `apps/web/src/features/agents/agent-detail.tsx`

- [ ] 详情页拆分为 tabs：
  - **概览**：Agent 基本信息 + 当前版本摘要 + 最近运行
  - **配置**：API 地址、认证、超时、最大步数
  - **版本历史**：版本列表 + 操作（查看/设置当前/设置基线）
  - **运行记录**：关联的运行列表
  - **产物**：关联的产物下载列表
- [ ] 顶部固定：Agent 名称、状态、当前版本、基线版本、主要操作

#### 1.5 版本列表与详情

**Files:**
- Create: `apps/web/src/features/agents/version-list.tsx`
- Create: `apps/web/src/features/agents/version-detail-drawer.tsx`

- [ ] 版本列表：版本号、状态（草稿/已发布）、创建时间、当前/基线标记、操作
- [ ] 版本详情抽屉：完整字段展示（模型参数、工具 Schema、超时/步数/成本）
- [ ] 版本对比入口：选择两个版本，展示 diff

#### 1.6 版本对比视图

**Files:**
- Create: `apps/web/src/features/agents/version-diff-view.tsx`

- [ ] 左右两列对比：版本 A vs 版本 B
- [ ] 变更字段高亮（增加/删除/修改）
- [ ] 嵌套 JSON 字段展开显示

**验收标准：**
- 后端：ruff / mypy / 迁移 / 单元测试通过
- 前端：TypeCheck / Lint / E2E 通过
- Agent 版本 CRUD + 对比 + 详情 tabs 完整可用

---

## 阶段二：测试数据集与用例增强（PRD 8.3）

**目标：** 用例支持高级字段、多格式导入导出、版本分组。

### 后端任务

#### 2.1 用例字段扩展

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/datasets/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/datasets/infrastructure/persistence/models.py`
- Create: `apps/control-api/migrations/versions/0007_test_case_fields.py`

- [ ] TestCase 新增字段：
  - `initial_state`: JSON — 初始业务状态
  - `expected_outcome`: JSON — 预期输出结构
  - `assertions`: JSON — 确定性断言规则
  - `scorers`: JSON — 关联评分器列表
  - `security_policies`: JSON — 安全策略
  - `tags`: JSON — 标签列表
  - `priority`: str — 优先级（P0/P1/P2/P3）
  - `risk_level`: str — 风险等级（high/medium/low）
  - `difficulty`: str — 难度（easy/medium/hard）
  - `group`: str — 分组（train/validation/test）
- [ ] 迁移 0007：ALTER TABLE 新增字段

#### 2.2 从失败运行生成用例

**Files:**
- Create: `apps/control-api/src/agenttest/modules/datasets/application/generate_from_run.py`

- [ ] `POST /api/v1/projects/{project_id}/datasets/{dataset_id}/generate-from-run`
- [ ] 接收 `run_id`，查询失败 RunCases，生成用例草稿
- [ ] 自动填充：name（来自 case 名）、input、expected_outcome（来自错误信息）

#### 2.3 CSV 导入增强

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/datasets/application/import_export.py`

- [ ] CSV 字段映射：支持自定义列名到用例字段的映射
- [ ] 导入前校验：必填字段检查 + 类型检查
- [ ] 返回导入结果报告：成功数、失败数、失败原因列表

### 前端任务

#### 2.4 用例详情与编辑

**Files:**
- Create: `apps/web/src/features/datasets/test-case-detail.tsx`
- Create: `apps/web/src/features/datasets/test-case-form.tsx`

- [ ] 用例详情：完整字段展示
- [ ] 用例表单：分区表单（基本信息 / 输入数据 / 预期输出 / 断言 / 评分 / 安全策略）
- [ ] JSON 编辑器用于结构化字段

#### 2.5 批量操作

- [ ] 列表页多选 checkbox
- [ ] 批量删除 / 批量标签 / 批量导出
- [ ] 批量操作需展示影响范围确认

#### 2.6 导入向导

**Files:**
- Create: `apps/web/src/features/datasets/import-wizard.tsx`

- [ ] Step 1：选择文件（JSON/JSONL/CSV）
- [ ] Step 2：字段映射预览（CSV 时）
- [ ] Step 3：校验报告（成功/失败数 + 失败原因）
- [ ] Step 4：确认导入

**验收标准：**
- 用例完整字段 CRUD + 导入向导 + 失败用例生成通过

---

## 阶段三：测试环境管理（PRD 8.4）

**目标：** 环境模板管理，支持测试凭证和沙箱配置。

### 后端任务

#### 3.1 环境模板字段扩展

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/environments/domain/entities.py`
- Create: `apps/control-api/migrations/versions/0008_environment_fields.py`

- [ ] EnvironmentTemplate 新增字段：
  - `credentials`: JSON — 加密存储的测试凭证
  - `mock_services`: JSON — Mock 服务配置
  - `random_seed`: int | null — 固定随机种子
  - `dependency_versions`: JSON — 依赖版本锁定
  - `sandbox_config`: JSON — 沙箱参数
  - `cleanup_script`: str — 清理脚本
- [ ] 凭证字段读取时脱敏（仅显示掩码，不暴露明文）

#### 3.2 环境快照 API

**Files:**
- Create: `apps/control-api/src/agenttest/modules/environments/application/snapshot.py`

- [ ] `POST /api/v1/projects/{project_id}/environments/{env_id}/snapshots` 创建快照
- [ ] `POST /api/v1/projects/{project_id}/environments/{env_id}/snapshots/{snap_id}/restore` 恢复
- [ ] `DELETE /api/v1/projects/{project_id}/environments/{env_id}/snapshots/{snap_id}` 清理

#### 3.3 测试账号管理

**Files:**
- Create: `apps/control-api/src/agenttest/modules/environments/domain/test_accounts.py`

- [ ] `POST /api/v1/projects/{project_id}/test-accounts` 创建测试账号
- [ ] `GET /api/v1/projects/{project_id}/test-accounts` 列表
- [ ] 凭证字段加密存储

### 前端任务

#### 3.4 环境管理页面

**Files:**
- Create: `apps/web/src/features/environments/environment-list.tsx`
- Create: `apps/web/src/features/environments/environment-detail.tsx`
- Add nav: app-shell 新增"环境与凭证"导航

- [ ] 环境模板列表 + CRUD
- [ ] 环境模板编辑器：凭证管理（掩码显示）、Mock 配置、沙箱参数
- [ ] 测试账号管理子页面

**验收标准：**
- 环境模板 CRUD + 凭证加密 + 快照 API 通过

---

## 阶段四：测试计划增强（PRD 8.5）

**目标：** 测试计划支持完整配置项（并发、超时、评分器、门禁）。

### 后端任务

#### 4.1 测试计划字段扩展

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/test_plans/domain/entities.py`
- Create: `apps/control-api/migrations/versions/0009_test_plan_fields.py`

- [ ] TestPlanVersion 新增字段：
  - `concurrency`: int — 并发数（默认 1）
  - `max_retries`: int — 最大重试次数（默认 0）
  - `timeout_seconds`: int — 单次执行超时（默认 300）
  - `scorer_weights`: JSON — 评分器权重配置
  - `pass_threshold`: float — 通过阈值（0.0-1.0，默认 0.8）
  - `cost_budget`: float | null — 成本预算（单位：分）
  - `baseline_run_id`: str | null — 基线运行 ID
  - `release_gate`: JSON — 发布门禁条件

#### 4.2 试运行 API

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_plans/application/dry_run.py`

- [ ] `POST /api/v1/projects/{project_id}/test-plans/{plan_id}/versions/{version_id}/dry-run`
- [ ] 返回：预计用例数、预计执行时间、预计模型成本、配置校验结果
- [ ] 校验：关联的 Agent 版本/数据集版本/环境是否有效

### 前端任务

#### 4.3 测试计划编辑器重做

**Files:**
- Modify: `apps/web/src/features/test-plans/test-plan-detail.tsx`
- Create: `apps/web/src/features/test-plans/test-plan-editor.tsx`

- [ ] 分区表单：基本信息 / 执行配置 / 评分配置 / 门禁配置
- [ ] 执行配置区：并发数、重试、超时
- [ ] 评分配置区：评分器选择 + 权重滑块 + 通过阈值
- [ ] 门禁配置区：基线运行选择、成功率阈值、成本预算
- [ ] 高级配置默认折叠，关键字段可见
- [ ] 试运行按钮：点击后弹出预计用例数 / 时间 / 成本

**验收标准：**
- 完整测试计划编辑器 + 试运行 + 模板保存通过

---

## 阶段五：Trace 与可观测性（PRD 8.8）

**目标：** 运行详情页支持完整 Trace 树和时间线。

### 后端任务

#### 5.1 Trace 数据模型增强

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/models.py`
- Create: `apps/control-api/migrations/versions/0010_trace_fields.py`

- [ ] RunEvent 新增字段：
  - `parent_event_id`: str | null — 父 Span ID
  - `event_type`: str — 类型（step/tool_call/model_request/result/error）
  - `duration_ms`: int | null — 耗时
  - `token_count`: int | null — Token 消耗
  - `cost`: float | null — 费用
  - `metadata`: JSON — 额外元数据
- [ ] 迁移 0010：ALTER TABLE 新增字段

#### 5.2 Trace 对比 API

**Files:**
- Create: `apps/control-api/src/agenttest/modules/runs/application/trace_diff.py`

- [ ] `GET /api/v1/projects/{project_id}/runs/{run_a_id}/diff/{run_b_id}`
- [ ] 返回：逐用例执行时间差异、评分差异、状态差异

### 前端任务

#### 5.3 Trace 树组件

**Files:**
- Create: `apps/web/src/features/runs/trace-tree.tsx`
- Create: `apps/web/src/features/runs/trace-timeline.tsx`

- [ ] Trace 树：可展开的父子 Span 结构，显示类型、耗时、Token
- [ ] 时间线：水平轴展示执行顺序，颜色区分类型
- [ ] 工具调用详情面板：参数 / 结果 / 错误 / 耗时

#### 5.4 运行详情页重组

**Files:**
- Modify: `apps/web/src/features/runs/run-detail.tsx`

- [ ] tabs：概览 / 用例列表 / Trace / 产物 / 审计
- [ ] 概览 tab：进度、统计、执行摘要
- [ ] 用例列表 tab：状态/评分/操作
- [ ] Trace tab：Trace 树 + 时间线

**验收标准：**
- Trace 树 + 时间线 + 运行详情 tabs 完整可用

---

## 阶段六：断言与评分器管理（PRD 8.9）

**目标：** 评分器可配置，结果展示完整。

### 后端任务

#### 6.1 评分器配置模块

**Files:**
- Create: `apps/control-api/src/agenttest/modules/scorers/`（完整 DDD 模块）
- Create: `apps/control-api/migrations/versions/0011_scorers.py`

- [ ] Scorer 实体：name、type（rule/model/reference）、weight、threshold、config_json
- [ ] CRUD API：`/api/v1/projects/{project_id}/scorers`
- [ ] 评分执行引擎：按配置调用评分器，记录证据和置信度
- [ ] 评分结果结构：score、pass、explanation、evidence、confidence、scorer_version

### 前端任务

#### 6.2 评分器管理页面

**Files:**
- Create: `apps/web/src/features/scorers/scorer-list.tsx`
- Create: `apps/web/src/features/scorers/scorer-editor.tsx`
- Add nav: app-shell 新增"评分器"导航

- [ ] 评分器列表：名称、类型、权重、阈值、状态
- [ ] 评分器编辑器：类型选择 + 权重配置 + 阈值设置
- [ ] 运行结果评分展示：每个用例的多维度评分面板

**验收标准：**
- 评分器 CRUD + 评分执行 + 结果展示通过

---

## 阶段七：实验与版本对比（PRD 8.10）

**目标：** A/B 对比分析，退化检测。

### 后端任务

#### 7.1 实验对比 API

**Files:**
- Create: `apps/control-api/src/agenttest/modules/experiments/`（完整 DDD 模块）
- Create: `apps/control-api/migrations/versions/0012_experiments.py`

- [ ] Experiment 实体：name、run_a_id、run_b_id、status、result_json
- [ ] `POST /api/v1/projects/{project_id}/experiments` 创建对比实验
- [ ] `GET /api/v1/projects/{project_id}/experiments/{id}` 获取对比结果
- [ ] 逐用例对比：评分差异、状态差异、耗时差异
- [ ] 统计：平均值、方差、P50/P95、提升/退化/无变化分类

### 前端任务

#### 7.2 实验对比页面

**Files:**
- Create: `apps/web/src/features/experiments/experiment-list.tsx`
- Create: `apps/web/src/features/experiments/experiment-detail.tsx`
- Add nav: app-shell 新增"实验对比"导航

- [ ] 实验列表 + 创建对话框
- [ ] 对比结果：逐用例对比表，退化项高亮
- [ ] 统计摘要：总体趋势、关键指标变化、退化警告

**验收标准：**
- A/B 对比 + 退化检测 + 统计展示通过

---

## 阶段八：人工审核（PRD 8.11）

**目标：** 低置信度结果自动收集，支持人工评分。

### 后端任务

#### 8.1 审核任务模块

**Files:**
- Create: `apps/control-api/src/agenttest/modules/reviews/`（完整 DDD 模块）
- Create: `apps/control-api/migrations/versions/0013_reviews.py`

- [ ] ReviewTask 实体：run_case_id、status（pending/approved/rejected/skipped）、reviewer_id、score、opinion、rubric_scores
- [ ] `POST /api/v1/projects/{project_id}/reviews/auto-enqueue` 低置信度自动入队
- [ ] `POST /api/v1/projects/{project_id}/reviews/{id}/score` 人工评分
- [ ] 审核一致性统计

### 前端任务

#### 8.2 审核工作台

**Files:**
- Create: `apps/web/src/features/reviews/review-workbench.tsx`
- Add nav: app-shell 新增"人工审核"导航

- [ ] 审核工作台：左侧任务列表 + 右侧用例详情 + 评分面板
- [ ] 评分方式：单结果打分 / A/B 偏好选择 / Rubric 多维评分
- [ ] 支持审核意见、跳过、批量处理

**验收标准：**
- 自动入队 + 审核工作台 + Rubric 评分通过

---

## 阶段九：安全测试（PRD 9.1）

**目标：** 安全测试页面完整化，扫描结果分类展示。

### 后端任务

#### 9.1 安全扫描执行

**Files:**
- Create: `apps/control-api/src/agenttest/modules/security/application/scan_runner.py`

- [ ] `POST /api/v1/projects/{project_id}/security/scan` 触发 Promptfoo 扫描
- [ ] `GET /api/v1/projects/{project_id}/security/scan/{scan_id}` 查询结果
- [ ] 安全报告分类存储：injection / leak / jailbreak

### 前端任务

#### 9.2 安全测试页面

**Files:**
- Create: `apps/web/src/features/security/security-scan.tsx`
- Add nav: app-shell 新增"安全测试"导航

- [ ] 扫描结果列表：注入 / 泄露 / 越狱分类
- [ ] 安全报告详情：攻击向量、响应、评分
- [ ] 扫描触发按钮 + 扫描进度展示

**验收标准：**
- 安全扫描执行 + 结果展示 + 报告详情通过

---

## 阶段十：发布门禁（PRD 8.12）

**目标：** CI 门禁配置与管理。

### 后端任务

#### 10.1 发布门禁模块

**Files:**
- Create: `apps/control-api/src/agenttest/modules/gates/`（完整 DDD 模块）
- Create: `apps/control-api/migrations/versions/0014_release_gates.py`

- [ ] ReleaseGate 实体：project_id、success_rate_threshold、critical_cases、cost_limit、security_threshold
- [ ] `POST /api/v1/projects/{project_id}/gates/evaluate` 门禁评估
- [ ] `POST /api/v1/projects/{project_id}/gates/{id}/exempt` 临时豁免
- [ ] 豁免操作记录审计日志

### 前端任务

#### 10.2 发布门禁页面

**Files:**
- Create: `apps/web/src/features/gates/gate-list.tsx`
- Create: `apps/web/src/features/gates/gate-editor.tsx`
- Add nav: app-shell 新增"发布门禁"导航

- [ ] 门禁条件编辑器
- [ ] 门禁评估结果：通过 / 不通过 + 原因明细
- [ ] 豁免管理 + 审计日志

**验收标准：**
- 门禁配置 + 自动评估 + 豁免管理通过

---

## 阶段十一：测试 Agent 对话入口（PRD 6.6）

**目标：** 左侧导航 / 主页增加对话入口，自然语言驱动测试。

### 前端任务

#### 11.1 测试 Agent 对话界面

**Files:**
- Create: `apps/web/src/features/test-agent/chat-screen.tsx`
- Create: `apps/web/src/features/test-agent/plan-card.tsx`

- [ ] 对话界面：消息列表 + 输入框 + 计划卡片
- [ ] 计划卡片：可展开的结构化配置（Agent 版本、数据集、评分器、预算）
- [ ] 运行进度实时展示

### 后端任务

#### 11.2 对话 API

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_agent/`（完整 DDD 模块）

- [ ] `POST /api/v1/projects/{project_id}/test-agent/chat` 发送自然语言指令
- [ ] 返回结构化测试计划草稿
- [ ] `POST /api/v1/projects/{project_id}/test-agent/confirm` 确认执行

**验收标准：**
- 对话入口 + 计划生成 + 实时进度通过

---

## 执行节奏

每阶段完成后：
1. 后端：ruff / mypy / 迁移 / 单元测试通过
2. 前端：TypeCheck / Lint / E2E 通过
3. 更新 `docs/当前任务.md` 和 `docs/开发进度与变更记录.md`
4. 合并至 main 并推送
5. 进入下一阶段
