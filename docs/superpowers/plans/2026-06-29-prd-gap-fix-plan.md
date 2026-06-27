# PRD 全量差距修复计划

基于 PRD 全量差距分析（2026-06-29），按优先级分批修复。

---

## P0 — MVP 上线必做

### 1. 凭证脱敏（PRD 8.4） ✅ 已完成
- Commit: 784b1c1
- 范围：环境模板 config 字段 API 响应脱敏
- 后端：`credential_mask.py` 深度递归掩码（password/api_key/token/secret/auth 字段）
- 测试：9 个单元测试
- 验收：API 返回掩码值，非明文

### 2. 登录失败锁定（PRD 8.1）
- 范围：连续登录失败达阈值后自动锁定账号
- 后端：`identity` 模块新增 `failed_login_count` + `locked_until` 字段
- 迁移：ALTER TABLE users 新增列
- 验收：连续 5 次失败后锁定 15 分钟

### 3. 测试账号管理 API（PRD 8.4）
- 范围：独立的测试账号 CRUD + 凭证加密
- 后端：新建 `test_accounts` DDD 模块（entity / repo / API）
- 迁移：CREATE TABLE test_accounts
- 前端：环境模板页新增"测试账号"子页面
- 验收：CRUD + 凭证加密存储 + 项目隔离

### 4. 安全扫描实际执行（PRD 9.1-9.3）
- 范围：Promptfoo 适配器集成，替换 Mock 数据
- 后端：新建 `security/adapters/promptfoo_adapter.py`
- 修改：`security/api/scan_router.py` 调用适配器而非返回 mock
- 验收：POST /security/scans 实际执行 Promptfoo 并返回真实结果

### 5. Playwright Runner（PRD 8.7）
- 范围：浏览器自动化执行引擎
- 后端：新建 `workers/playwright-runner/` Temporal Worker
- 前端：浏览器用例类型支持 + 截图展示
- 验收：可执行 Playwright 用例并返回截图

---

## P1 — 核心体验提升

### 6. 测试 Agent Chat LLM 集成（PRD 6.6）
- 范围：替换 Mock 响应为 LLM 调用
- 后端：`test_agent` 模块接入 LLM API（MIMO / OpenAI）
- 修改：`test_agent/api/router.py` 的 `_generate_mock_plan` → LLM 调用
- 会话存储：内存 → 数据库持久化
- 验收：自然语言输入 → LLM 生成结构化计划

### 7. 多轮会话 API 执行（PRD 8.6）
- 范围：AgentRequest 支持多轮对话
- 后端：`runs` 模块新增 `session_id` 字段，支持上下文传递
- 验收：多轮对话中 Agent 可引用历史上下文

### 8. 实时进度推送（PRD 8.6）
- 范围：SSE/WebSocket 运行进度实时推送
- 后端：新增 `/runs/{id}/stream` SSE 端点
- 前端：运行详情页 SSE 实时刷新
- 验收：运行进度实时更新，无需轮询

### 9. 画布 Agent Adapter 实现（PRD 10.1）
- 范围：CanvasAgentAdapter 具体实现
- 后端：`plugins/canvas/` 实现节点创建、连线、执行
- 验收：可通过 API 操作画布节点和连线

### 10. 视频评分能力（PRD 10.4）
- 范围：视频镜头数、运动、连贯性、画面质量评分
- 后端：`scorers` 模块新增视频评分器
- 验收：视频输入 → 评分结果

---

## P2 — 后续迭代

### 11. 安全框架适配器预留（PRD 9.3）
- Garak / PyRIT / AgentDojo 适配器接口预留

### 12. 画布断言补充（PRD 10.3）
- 节点创建/执行顺序断言
- 失败/错误节点检测
- 必需输入/输出断言
- 布局重叠检测

### 13. 测试账号与环境模板关联
- 测试账号可关联到环境模板
- Mock 服务管理

### 14. Webhook 回调任务（PRD 8.6）
- 任务完成时通过 Webhook 通知

### 15. 网络 Mock 和异常注入（PRD 8.7）
- 浏览器测试网络层 Mock

---

## 执行节奏

每个 P0 任务：
1. 创建开发分支
2. 先写测试，再实现
3. ruff + mypy + 152+ tests 通过
4. 合并到 main 并推送
5. 更新本文档状态
