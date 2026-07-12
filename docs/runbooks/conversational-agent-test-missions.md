# 对话式 Agent 全链路测试任务运行手册

本手册用于运行和排查 `Test Mission`。任务以不可变 Revision 为执行快照，经一次普通确认后创建或复用平台资产，并把 Run、证据、评分、安全发现、审核、报告和发布门禁关联回 Mission。任何外部失败必须保留真实状态，不得以 Mock 或前端展示代替成功。

## 1. 安全与权限

- 所有 Mission、Fact、Revision、Event、Stage Receipt 和 Asset Link 都必须按 `project_id` 隔离。
- 密码、Token、Cookie 和明文 Browser Auth State 不得进入对话、Revision、日志、Trace 或 Temporal History；任务只保存凭证或 Browser Profile 引用。
- 默认动作范围为只读。删除、支付、发布、权限修改和对外发送仍需要单独高风险确认。
- URL 探测仅允许 HTTP(S)，校验解析地址和重定向，默认拒绝回环、内网、链路本地及云元数据地址；测试环境显式允许的 Fake Target 除外。

## 2. 前置条件与启动

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml up -d
uv run python scripts/wait_for_services.py
uv run alembic -c apps/control-api/alembic.ini upgrade head
```

随后分别启动 Control API、API Runner 和 Web；命令及环境变量沿用 `docs/runbooks/tapnow-production-testing.md`。确认 Control API、Web、MinIO、PostgreSQL 和 Temporal 健康后再创建 Mission。

## 3. 正常流程

1. 用户在测试 Agent 对话中提供目标 URL 或平台 Agent，以及一句测试目标。
2. 系统合并同项目资产并执行只读探测，只追问仍然缺失的目标、访问方式、测试目标或安全范围。
3. 预检卡展示执行通道、推断用例、预算、动作边界和资产决策；确认哈希与 Revision 内容必须一致。
4. `confirm-start` 以幂等键启动 `TestMissionWorkflow`。重复确认返回同一任务，不得创建重复 Run。
5. Workflow 按 `provision → start_run → await_run → close_loop` 执行；每阶段保存回执，Worker 只调用带内部令牌的 Control API，不连接业务数据库。
6. 完成后从 Mission 进入关联 Run、数据集、报告、审核和发布门禁检查结果。

## 4. 暂停、恢复与取消

- 登录态失效：Mission 进入 `needs_attention`。在原 Browser Profile 完成登录后点击“登录完成，继续测试”；恢复次数进入 Activity 输入，已成功阶段不重跑。
- 外部额度不足：保留真实错误分类，补充额度后恢复或创建新 Revision；不得改写已确认快照。
- 取消：调用 Mission cancel，Workflow 停止派发新阶段；已经创建的资产、Run 和证据保留。重复取消保持幂等。
- Worker/Control API 重启：Temporal 从历史恢复；阶段回执以 `revision_id + stage` 去重。

## 5. 诊断

依次检查 Mission 状态、事件序列、当前 Revision 哈希、Stage Receipt、关联 Run 和 RunCase 证据。常见分类：

- `auth_expired`：重新验证 Browser Profile 后恢复。
- `quota_exceeded`：补充目标或模型额度，记录外部门禁阻塞。
- `target_error`：目标产品真实失败，可转入自动生成的失败回归数据集。
- `platform_error`：检查 Control API/Temporal/Worker 日志和内部令牌，但日志中不得出现秘密。
- `quality_failed` / 安全 Finding：技术执行可以成功，但审核或发布门禁必须独立阻断。

## 6. 验证与回滚

发布前执行实施计划中的 Python、架构、数据库、前端、Playwright 和 API 漂移门禁。数据库迁移按 Alembic 历史处理；回滚应用前停止新 Mission，等待或取消活动 Workflow，并导出需要保留的 Mission/Run 审计证据。不得改写已发布 Revision 或迁移文件。

真实目标验收必须使用获准的专用测试账号和足够额度，完成一次只读成功 Run，并确认 Evidence、Artifact、评分、失败回归、报告和 Gate 均已落库。账号、登录态或额度不可用时，将任务标记为外部阻塞，不能宣称生产门禁通过。
