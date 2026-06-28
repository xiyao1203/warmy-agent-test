# PRD 全量功能深化实施计划

基于 2026-06-28 PRD 差距分析，制定详细的分阶段实施计划，覆盖 7 大功能差距。

---

## 1. 计划概览

| 阶段 | 任务 | 预计工期 | 依赖 | 优先级 |
|------|------|----------|------|--------|
| 阶段一 | 结果工作台优化 | 2 天 | 无 | 高 |
| 阶段二 | 实验对比统计增强 | 1.5 天 | 阶段一 | 高 |
| 阶段三 | 人工审核深度集成 | 2 天 | 阶段一 | 高 |
| 阶段四 | 测试计划高级配置 | 1.5 天 | 无 | 中 |
| 阶段五 | Trace 可观测性增强 | 2 天 | 阶段一 | 中 |
| 阶段六 | 对话 Agent 智能协作 | 1.5 天 | 阶段二 | 低 |
| 阶段七 | 报告导出标准化 | 1.5 天 | 阶段二 | 低 |

**总预计工期：12-13 天**

---

## 2. 阶段一：结果工作台优化（2 天）

### 2.1 目标

实现 PRD 6.3 要求的三栏布局结果工作台，支持 Trace 树形可视化、状态差异对比和产物预览。

### 2.2 任务清单

#### Task 1.1：Trace 树形可视化组件（1 天）

**目标：** 实现 Agent Trace 的树形展示，支持父子关系、展开/折叠和搜索。

**文件变更：**
- `apps/web/src/features/runs/trace-tree.tsx`（新增）
- `apps/web/src/features/runs/trace-node.tsx`（新增）
- `apps/web/src/features/runs/trace-search.tsx`（新增）
- `apps/web/src/features/runs/tests/trace-tree.test.tsx`（新增）

**实现要求：**
1. 使用 React Flow（动态加载）渲染 Trace 树
2. 支持 Span 父子关系展示
3. 支持展开/折叠节点
4. 支持按关键字搜索 Trace
5. 高亮显示错误和超时节点
6. 支持点击查看 Span 详情

**验收标准：**
- [ ] Trace 树正确展示父子关系
- [ ] 展开/折叠功能正常
- [ ] 搜索功能可定位到匹配节点
- [ ] 错误节点有明显视觉标识
- [ ] 组件测试通过

**测试命令：**
```bash
pnpm --filter @warmy/web test -- --testPathPattern=trace-tree
```

#### Task 1.2：结果工作台三栏布局（0.5 天）

**目标：** 实现左中右三栏布局，支持用例列表、详情展示和评分面板。

**文件变更：**
- `apps/web/src/features/runs/run-result-workbench.tsx`（重构）
- `apps/web/src/features/runs/case-list-panel.tsx`（新增）
- `apps/web/src/features/runs/case-detail-panel.tsx`（新增）
- `apps/web/src/features/runs/score-panel.tsx`（新增）

**实现要求：**
1. 左栏：用例列表，支持筛选和批量选择
2. 中栏：当前用例详情（输入、输出、Trace、产物）
3. 右栏：评分结果、失败分类、审核意见
4. 支持面板宽度调整
5. 支持面板折叠

**验收标准：**
- [ ] 三栏布局正确显示
- [ ] 点击用例列表切换详情
- [ ] 面板宽度可调整
- [ ] 面板可折叠
- [ ] 组件测试通过

**测试命令：**
```bash
pnpm --filter @warmy/web test -- --testPathPattern=run-result-workbench
```

#### Task 1.3：产物预览集成（0.5 天）

**目标：** 实现图片、视频、文件的预览和下载功能。

**文件变更：**
- `apps/web/src/features/runs/artifact-preview.tsx`（新增）
- `apps/web/src/features/runs/image-viewer.tsx`（新增）
- `apps/web/src/features/runs/video-player.tsx`（新增）
- `apps/web/src/features/runs/tests/artifact-preview.test.tsx`（新增）

**实现要求：**
1. 图片预览：支持缩放、全屏
2. 视频播放：支持播放/暂停、进度条
3. 文件下载：支持下载到本地
4. 支持多种文件格式（jpg, png, mp4, json, log）
5. 动态加载重型组件

**验收标准：**
- [ ] 图片可预览和缩放
- [ ] 视频可播放
- [ ] 文件可下载
- [ ] 支持常见文件格式
- [ ] 组件测试通过

**测试命令：**
```bash
pnpm --filter @warmy/web test -- --testPathPattern=artifact-preview
```

### 2.3 验证命令

```bash
# 类型检查
pnpm --filter @warmy/web typecheck

# Lint 检查
pnpm --filter @warmy/web lint

# 单元测试
pnpm --filter @warmy/web test

# 构建验证
pnpm --filter @warmy/web build
```

---

## 3. 阶段二：实验对比统计增强（1.5 天）

### 3.1 目标

实现 PRD 8.10 要求的统计分析功能，支持 P50/P95 计算、退化项高亮和按场景聚合。

### 3.2 任务清单

#### Task 2.1：统计分析后端 API（0.5 天）

**目标：** 实现实验统计分析 API，返回平均值、方差、P50、P95。

**文件变更：**
- `apps/control-api/src/agenttest/modules/experiments/domain/statistics.py`（新增）
- `apps/control-api/src/agenttest/modules/experiments/api/router.py`（修改）
- `apps/control-api/tests/unit/experiments/test_statistics.py`（新增）

**API 端点：**
```
GET /api/v1/projects/{project_id}/experiments/{experiment_id}/statistics
```

**响应格式：**
```json
{
  "total_cases": 100,
  "passed": 85,
  "failed": 15,
  "pass_rate": 0.85,
  "statistics": {
    "latency": {
      "avg": 1200,
      "p50": 1000,
      "p95": 2500,
      "std_dev": 300
    },
    "score": {
      "avg": 0.82,
      "p50": 0.85,
      "p95": 0.65,
      "std_dev": 0.12
    },
    "cost": {
      "avg": 0.05,
      "p50": 0.04,
      "p95": 0.12,
      "total": 5.0
    }
  },
  "degradation": [
    {
      "case_id": "case-001",
      "metric": "score",
      "baseline": 0.9,
      "current": 0.6,
      "change": -0.33
    }
  ]
}
```

**实现要求：**
1. 计算平均值、方差、P50、P95
2. 识别退化项（变化超过阈值）
3. 支持按场景、风险等级聚合
4. 单元测试覆盖边界情况

**验收标准：**
- [ ] API 返回正确的统计数据
- [ ] P50/P95 计算准确
- [ ] 退化项正确识别
- [ ] 5 个单元测试通过

**测试命令：**
```bash
uv run pytest apps/control-api/tests/unit/experiments/test_statistics.py -v
```

#### Task 2.2：对比 UI 增强（1 天）

**目标：** 实现实验对比页面，支持退化项高亮、提升项标记和聚合视图。

**文件变更：**
- `apps/web/src/features/experiments/experiment-compare.tsx`（重构）
- `apps/web/src/features/experiments/degradation-highlight.tsx`（新增）
- `apps/web/src/features/experiments/aggregation-view.tsx`（新增）
- `apps/web/src/features/experiments/tests/experiment-compare.test.tsx`（新增）

**实现要求：**
1. 退化项使用红色背景高亮
2. 提升项使用绿色背景标记
3. 支持按场景/风险等级聚合视图
4. 支持 P50/P95 统计卡片
5. 支持导出统计报告

**验收标准：**
- [ ] 退化项高亮显示
- [ ] 提升项标记显示
- [ ] 聚合视图按场景分组
- [ ] 统计卡片显示 P50/P95
- [ ] 组件测试通过

**测试命令：**
```bash
pnpm --filter @warmy/web test -- --testPathPattern=experiment-compare
```

### 3.3 验证命令

```bash
# 后端测试
uv run pytest apps/control-api/tests/unit/experiments/ -v

# 前端测试
pnpm --filter @warmy/web test

# 类型检查
pnpm --filter @warmy/web typecheck
```

---

## 4. 阶段三：人工审核深度集成（2 天）

### 4.1 目标

实现 PRD 8.11 要求的人工审核功能，支持低置信度自动收集、A/B 偏好选择和一致性统计。

### 4.2 任务清单

#### Task 3.1：低置信度自动收集逻辑（0.5 天）

**目标：** 实现评分完成后自动将低置信度结果加入审核队列。

**文件变更：**
- `apps/control-api/src/agenttest/modules/reviews/domain/auto_collector.py`（新增）
- `apps/control-api/src/agenttest/modules/reviews/infrastructure/services.py`（修改）
- `apps/control-api/tests/unit/reviews/test_auto_collector.py`（新增）

**触发规则：**
1. 评分置信度 < 0.7
2. 评分冲突（不同评分器结果差异 > 0.3）
3. 高风险用例（标记为 high_risk）
4. 安全测试发现

**实现要求：**
1. 评分完成后异步触发收集
2. 自动创建 ReviewTask
3. 设置优先级（置信度越低，优先级越高）
4. 发送通知（可选）

**验收标准：**
- [ ] 低置信度结果自动入队
- [ ] 评分冲突结果自动入队
- [ ] 高风险用例自动入队
- [ ] 优先级正确设置
- [ ] 5 个单元测试通过

**测试命令：**
```bash
uv run pytest apps/control-api/tests/unit/reviews/test_auto_collector.py -v
```

#### Task 3.2：A/B 偏好选择 UI（1 天）

**目标：** 实现人工审核的 A/B 偏好选择界面。

**文件变更：**
- `apps/web/src/features/reviews/ab-preference.tsx`（新增）
- `apps/web/src/features/reviews/review-workbench.tsx`（重构）
- `apps/web/src/features/reviews/tests/ab-preference.test.tsx`（新增）

**实现要求：**
1. 左右对比展示两个版本的输出
2. 支持选择 A 更好、B 更好、都好、都差
3. 支持添加审核意见
4. 支持查看 Trace 差异
5. 支持快捷键操作

**验收标准：**
- [ ] A/B 对比正确显示
- [ ] 偏好选择功能正常
- [ ] 审核意见可保存
- [ ] 快捷键可用
- [ ] 组件测试通过

**测试命令：**
```bash
pnpm --filter @warmy/web test -- --testPathPattern=ab-preference
```

#### Task 3.3：Rubric 多维评分配置（0.5 天）

**目标：** 实现 Rubric 多维评分配置和展示。

**文件变更：**
- `apps/web/src/features/reviews/rubric-editor.tsx`（新增）
- `apps/web/src/features/reviews/rubric-display.tsx`（新增）
- `apps/web/src/features/reviews/tests/rubric-editor.test.tsx`（新增）

**实现要求：**
1. 支持配置多个评分维度（质量、准确性、安全性等）
2. 每个维度支持 1-5 分评分
3. 支持添加评分说明
4. 支持查看历史评分

**验收标准：**
- [ ] 多维评分配置正常
- [ ] 评分可保存
- [ ] 历史评分可查看
- [ ] 组件测试通过

**测试命令：**
```bash
pnpm --filter @warmy/web test -- --testPathPattern=rubric-editor
```

#### Task 3.4：多人审核一致性统计（0.5 天，可选）

**目标：** 实现多人审核的一致性统计（Kappa 系数）。

**文件变更：**
- `apps/control-api/src/agenttest/modules/reviews/api/consistency.py`（新增）
- `apps/web/src/features/reviews/consistency-stats.tsx`（新增）

**API 端点：**
```
GET /api/v1/projects/{project_id}/reviews/consistency
```

**实现要求：**
1. 计算 Cohen's Kappa 系数
2. 识别分歧案例
3. 展示一致性趋势

**验收标准：**
- [ ] Kappa 系数计算正确
- [ ] 分歧案例可识别
- [ ] 统计数据可展示

### 4.3 验证命令

```bash
# 后端测试
uv run pytest apps/control-api/tests/unit/reviews/ -v

# 前端测试
pnpm --filter @warmy/web test

# 类型检查
pnpm --filter @warmy/web typecheck
```

---

## 5. 阶段四：测试计划高级配置（1.5 天）

### 5.1 目标

实现 PRD 8.5 要求的测试计划高级配置功能。

### 5.2 任务清单

#### Task 4.1：评分器权重配置 UI（0.5 天）

**文件变更：**
- `apps/web/src/features/test-plans/scorer-weight-config.tsx`（新增）
- `apps/web/src/features/test-plans/tests/scorer-weight-config.test.tsx`（新增）

**实现要求：**
1. 支持添加多个评分器
2. 每个评分器支持设置权重（0-100%）
3. 权重总和自动校验为 100%
4. 支持拖拽调整顺序

#### Task 4.2：阈值校验逻辑（0.5 天）

**文件变更：**
- `apps/control-api/src/agenttest/modules/test_plans/domain/threshold_validator.py`（新增）
- `apps/control-api/tests/unit/test_plans/test_threshold_validator.py`（新增）

**实现要求：**
1. 校验通过阈值（0-100%）
2. 校验成本预算（> 0）
3. 校验超时时间（> 0）
4. 校验重试次数（>= 0）

#### Task 4.3：成本预算控制（0.5 天）

**文件变更：**
- `apps/control-api/src/agenttest/modules/test_plans/domain/budget_controller.py`（新增）
- `apps/web/src/features/test-plans/budget-display.tsx`（新增）

**实现要求：**
1. 实时计算已用成本
2. 超过预算 80% 时警告
3. 超过预算 100% 时停止执行
4. 展示成本明细

### 5.3 验证命令

```bash
# 后端测试
uv run pytest apps/control-api/tests/unit/test_plans/ -v

# 前端测试
pnpm --filter @warmy/web test
```

---

## 6. 阶段五：Trace 可观测性增强（2 天）

### 6.1 目标

实现 PRD 8.8 要求的 OpenTelemetry 集成和 Trace 可视化。

### 6.2 任务清单

#### Task 5.1：OpenTelemetry 集成（1 天）

**文件变更：**
- `apps/control-api/src/agenttest/telemetry/`（新增目录）
- `apps/control-api/src/agenttest/telemetry/tracer.py`（新增）
- `apps/control-api/src/agenttest/telemetry/exporter.py`（新增）
- `apps/control-api/pyproject.toml`（修改，添加依赖）

**实现要求：**
1. 集成 OpenTelemetry SDK
2. 支持 Span 创建和传播
3. 支持导出到 Jaeger/Zipkin
4. 记录 Token、费用、延迟

#### Task 5.2：时间轴展示组件（0.5 天）

**文件变更：**
- `apps/web/src/features/runs/trace-timeline.tsx`（新增）
- `apps/web/src/features/runs/tests/trace-timeline.test.tsx`（新增）

**实现要求：**
1. 时间轴展示 Trace 执行顺序
2. 支持缩放和平移
3. 高亮显示关键 Span
4. 支持点击查看 Span 详情

#### Task 5.3：版本轨迹对比（0.5 天）

**文件变更：**
- `apps/web/src/features/runs/trace-comparison.tsx`（新增）

**实现要求：**
1. 对比两个版本的 Trace
2. 高亮显示差异
3. 支持逐 Span 对比

### 6.3 验证命令

```bash
# 后端测试
uv run pytest apps/control-api/tests/unit/ -v -k telemetry

# 前端测试
pnpm --filter @warmy/web test
```

---

## 7. 阶段六：对话 Agent 智能协作（1.5 天）

### 7.1 目标

实现 PRD 6.6 要求的对话式测试 Agent 智能推荐和成本估算。

### 7.2 任务清单

#### Task 6.1：智能推荐功能（0.5 天）

**文件变更：**
- `apps/control-api/src/agenttest/modules/test_agent/domain/recommender.py`（新增）

**实现要求：**
1. 基于历史推荐测试集
2. 基于 Agent 类型推荐环境模板
3. 基于用例特征推荐评分器

#### Task 6.2：成本估算卡片（0.5 天）

**文件变更：**
- `apps/web/src/features/test-agent/cost-estimate-card.tsx`（新增）

**实现要求：**
1. 计算用例数 × 单次成本
2. 估算 Token 消耗
3. 展示预计执行时间
4. 超过阈值时请求确认

#### Task 6.3：失败→回归转换（0.5 天）

**文件变更：**
- `apps/web/src/features/test-agent/failure-to-regression.tsx`（新增）

**实现要求：**
1. 一键转换失败用例为回归用例
2. 自动填充输入和预期输出
3. 支持批量转换

### 7.3 验证命令

```bash
# 后端测试
uv run pytest apps/control-api/tests/unit/test_agent/ -v

# 前端测试
pnpm --filter @warmy/web test
```

---

## 8. 阶段七：报告导出标准化（1.5 天）

### 8.1 目标

实现 PRD 8.12 要求的报告导出功能。

### 8.2 任务清单

#### Task 8.1：报告生成器（1 天）

**文件变更：**
- `apps/control-api/src/agenttest/modules/reports/`（新增目录）
- `apps/control-api/src/agenttest/modules/reports/generators/json_report.py`（新增）
- `apps/control-api/src/agenttest/modules/reports/generators/junit_report.py`（新增）
- `apps/control-api/src/agenttest/modules/reports/generators/html_report.py`（新增）
- `apps/control-api/src/agenttest/modules/reports/api/router.py`（新增）
- `apps/control-api/tests/unit/reports/test_generators.py`（新增）

**API 端点：**
```
GET /api/v1/projects/{project_id}/runs/{run_id}/reports/{format}
```

**支持格式：**
1. JSON：标准化测试结果格式
2. JUnit XML：CI/CD 集成
3. HTML：人类可读报告

#### Task 8.2：CI 集成（0.5 天）

**文件变更：**
- `docs/api/ci-integration.md`（新增）
- `.github/workflows/templates/`（新增目录）

**实现要求：**
1. GitHub Actions 模板
2. PR 评论格式
3. 状态检查集成

### 8.3 验证命令

```bash
# 后端测试
uv run pytest apps/control-api/tests/unit/reports/ -v
```

---

## 9. 里程碑与验收

### 9.1 阶段一验收（结果工作台）

- [ ] Trace 树正确展示父子关系
- [ ] 三栏布局可切换用例
- [ ] 产物可预览和下载
- [ ] 后端 160+ 测试通过
- [ ] 前端 40+ 测试通过

### 9.2 阶段二验收（实验对比）

- [ ] 统计 API 返回 P50/P95
- [ ] 退化项高亮显示
- [ ] 聚合视图按场景分组

### 9.3 阶段三验收（人工审核）

- [ ] 低置信度结果自动入队
- [ ] A/B 偏好选择可用
- [ ] 一致性统计可查看

### 9.4 阶段四验收（测试计划）

- [ ] 评分器权重可配置
- [ ] 阈值校验正常
- [ ] 成本预算可控制

### 9.5 阶段五验收（Trace）

- [ ] OpenTelemetry 集成正常
- [ ] 时间轴展示正常
- [ ] 版本对比可用

### 9.6 阶段六验收（对话 Agent）

- [ ] 推荐测试集/环境/Scorer
- [ ] 成本估算显示
- [ ] 失败→回归转换可用

### 9.7 阶段七验收（报告导出）

- [ ] JSON/JUnit/HTML 报告可下载
- [ ] GitHub Actions 模板可用

---

## 10. 风险与依赖

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| React Flow 性能问题 | 大量 Trace 节点时卡顿 | 虚拟化、分页加载 |
| OpenTelemetry 学习曲线 | 集成时间可能超预期 | 先实现基础功能，逐步增强 |
| LLM API 不可用 | 智能推荐功能无法实现 | 保留 Mock fallback |
| 统计计算复杂度 | P50/P95 计算可能有精度问题 | 使用成熟统计库 |

---

## 11. 优先级建议

**立即执行（1-2 周）：**
1. 阶段一：结果工作台优化
2. 阶段二：实验对比统计增强
3. 阶段三：人工审核深度集成

**中优先级（2-4 周）：**
4. 阶段四：测试计划高级配置
5. 阶段五：Trace 可观测性增强

**低优先级（后续迭代）：**
6. 阶段六：对话 Agent 智能协作
7. 阶段七：报告导出标准化

---

*文档生成时间：2026-06-29*
*基于 PRD V1.0（2026-06-25）*
*基于差距分析：2026-06-28-prd-gap-analysis-and-next-steps.md*
