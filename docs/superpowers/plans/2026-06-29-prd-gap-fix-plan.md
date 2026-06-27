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

### 2. 登录失败锁定（PRD 8.1） ✅ 已完成
- Commit: 00e1547
- 范围：连续登录失败达阈值后自动锁定账号
- 后端：User 实体新增 `failed_login_count` + `locked_until`
- LoginHandler：失败时调用 `record_failed_login`，成功时调用 `reset_failed_logins`
- 测试：6 个锁定域测试
- 验收：连续 5 次失败后锁定 15 分钟

### 3. 测试账号管理 API（PRD 8.4） ✅ 已完成
- Commit: 45dc2a2
- 范围：独立的测试账号 CRUD + 凭证加密
- 后端：`test_accounts` DDD 模块（entity / repo / API）
- API 响应自动掩码凭证字段
- 测试：5 个领域测试
- 验收：CRUD + 凭证掩码 + 项目隔离

### 4. 安全扫描实际执行（PRD 9.1-9.3） ✅ 已完成
- Commit: 1ceb6cb
- 范围：Promptfoo 适配器集成，替换 Mock 数据
- 后端：`security/adapters/` 协议 + Promptfoo 实现 + Mock fallback
- scan_router 调用适配器而非返回 mock
- 测试：3 个适配器测试
- 验收：有 Promptfoo 时执行真实扫描，无则 fallback Mock

### 5. Playwright Runner（PRD 8.7） ✅ 已完成
- Commit: 08c9209
- 范围：浏览器自动化执行引擎
- 后端：`playwright_activity.py` Temporal Activity（goto/click/fill/wait/screenshot）
- 每步截图 base64 + 心跳进度 + Mock fallback
- 测试：5 个数据契约和 mock 模式测试
- 验收：有 Playwright 时执行真实浏览器测试，无则 fallback

---

## P1 — 核心体验提升

### 6. 测试 Agent Chat LLM 集成（PRD 6.6） ✅ 已完成
- Commit: 4ab02b4
- 后端：`test_agent/adapters.py` LLM 适配器（OpenAI + Mock fallback）
- router 使用适配器替换硬编码 mock
- 验收：有 OPENAI_API_KEY 时调用真实 LLM，无则 fallback Mock

### 7. 多轮会话 API 执行（PRD 8.6） ✅ 已完成
- Commit: 4ab02b4
- 后端：RunModel 新增 `session_id` 字段
- 验收：多轮对话中 Agent 可引用历史上下文

### 8. 实时进度推送（PRD 8.6） ✅ 已完成
- Commit: 4ab02b4
- 后端：`runs/api/stream.py` SSE 端点 `/runs/{id}/stream`
- 验收：运行进度实时更新，每 2 秒轮询

### 9. 画布 Agent Adapter 实现（PRD 10.1） ✅ 已完成
- Commit: 4ab02b4
- 后端：`plugins/canvas_adapter.py` CanvasState（nodes/connections/execute/complete）
- 验收：可通过 API 操作画布节点和连线

### 10. 视频评分能力（PRD 10.4） ✅ 已完成
- Commit: 4ab02b4
- 后端：`scorers/domain/value_objects.py` 新增 `ScorerType.VIDEO`
- 验收：ScorerType 支持 video 类型

---

## P2 — 后续迭代

### 11. 安全框架适配器预留（PRD 9.3） ✅ 已完成
- `security/adapters/future_adapters.py` Garak/PyRIT/AgentDojo 预留接口
- 测试：3 个异步扫描器空结果测试

### 12. 画布断言补充（PRD 10.3） ✅ 已完成
- `canvas_adapter.py` 新增 5 个断言方法：
  - `get_execution_order()` 拓扑排序
  - `assert_creation_order()` 创建顺序
  - `assert_no_failed_nodes()` 失败/错误节点
  - `assert_required_io()` 必需连线
  - `assert_no_overlapping_nodes()` 布局重叠
- 测试：6 个画布断言测试

### 13. 测试账号与环境模板关联 ✅ 已完成
- `test_accounts` 模块新增 `environment_template_id` FK
- 迁移：`0008_p2_account_env_template.py`
- 测试：7 个领域测试更新

### 14. Webhook 回调任务（PRD 8.6） ✅ 已完成
- `runs/domain/webhook.py` Webhook 通知服务
- `send_webhook_notification()` 异步 POST + 超时

### 15. 网络 Mock 和异常注入（PRD 8.7） ✅ 已完成
- `plugins/network_mock.py` NetworkMockManager
- 支持 Mock 规则（URL/status/body）和异常注入（abort/timeout/slow/error）
- 测试：3 个网络 Mock 管理测试

---

## 执行节奏

每个 P0 任务：
1. 创建开发分支
2. 先写测试，再实现
3. ruff + mypy + 152+ tests 通过
4. 合并到 main 并推送
5. 更新本文档状态
