# TapNow 类 Agent 生产测试运行手册

本手册用于在 AgentTest 平台执行 TapNow 画布 Agent 的只读生产回归。执行结果必须回写 Run、RunCase、Artifact、评分、安全发现、人工审核和发布门禁；目标系统未登录、额度不足或权限不足时必须记录为阻塞或错误，不得伪造通过。

## 1. 安全边界

- 仅使用专用测试账号、专用项目和只读/低风险用例。
- 禁止付费、订阅、发布、删除、权限变更、成员变更和确认类操作。
- 目标账号密码仅保存为项目级加密凭证，Worker 通过短期凭证租约按 `project_id + run_id + run_case_id` 兑换。
- Workflow 快照、日志、Trace、Artifact 元数据和回调载荷不得包含密码、Cookie、Token 或加密凭证原文。
- 真实目标出现验证码、MFA、授权确认或收费提示时停止执行并进入人工处理。

## 2. 前置条件

1. TapNow 测试账号能够登录目标画布，并具有足够 Tapies/调用额度。
2. Agent 版本选择“TapNow 画布 Agent”，配置真实 `web_url`/`api_url`，`adapter_id` 为 `tapnow-canvas`，并发布不可变版本。
3. 在项目环境中创建两个加密凭证绑定：
   - `injection_name=username`：TapNow 登录邮箱或账号。
   - `injection_name=password`：TapNow 登录密码。
4. 将两个凭证 ID 绑定到 Agent 版本或运行环境；数据库与版本快照中只保存 ID 和脱敏元数据。
5. 发布数据集、用例、评分器和测试计划版本。生产回归优先使用 `browser`；需要先生成探索计划时使用 `codex_explore`。

## 3. 启动本地联调栈

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml up -d
uv run python scripts/wait_for_services.py
uv run alembic -c apps/control-api/alembic.ini upgrade head
```

分别启动控制面、Worker 和 Web：

```bash
set -a
source .env
set +a
export AGENTTEST_TEMPORAL_ADDRESS=localhost:7233
uv run uvicorn agenttest.main:app --app-dir apps/control-api/src --port 8181
```

```bash
set -a
source .env
set +a
export AGENTTEST_TEMPORAL_ADDRESS=localhost:7233
uv run python -m agenttest_api_runner.main
```

```bash
pnpm --filter @warmy/web dev --port 5175
```

健康检查：

```bash
curl -f http://localhost:8181/api/v1/health
curl -I http://localhost:5175/login
curl -f http://localhost:9000/minio/health/live
```

## 4. 执行顺序

1. 在运行中心选择已发布的 TapNow 测试计划版本并创建 Run。
2. Workflow 对 `adapter_id=tapnow-canvas*` 的目标启用 Canvas 执行；`codex_explore` 先生成只读计划，再执行真实 TapNow Activity。
3. Worker 兑换短期凭证、打开目标、登录、提交意图、等待完成、提取节点/连线/媒体并上传最终截图。
4. DeepEval 工具正确性指标以确定性本地模式执行，不读取进程级 OpenAI Key。
5. Promptfoo 使用真实 HTTP Provider 执行确定性安全断言；断言失败的非零退出码视为安全证据，而不是工具崩溃。
6. 控制面回写统一证据并触发评分聚合、Promptfoo Finding、人工审核收集和发布门禁。

## 5. 验收证据

一次可放行的真实 Run 至少应具备：

- Run 终态与所有 RunCase 终态一致。
- `execution_outcome=success`。
- Canvas 至少包含一个节点；连接按目标实际结果记录。
- 至少一个已持久化 Artifact，包含 ID、类型、大小和 SHA-256，不含 Base64 正文。
- DeepEval 分数与阈值结论。
- Promptfoo 安全扫描结果；高危/严重 Finding 必须阻断门禁。
- 低置信度、评分冲突或安全发现进入人工审核队列。
- 发布门禁引用 Run、评分、安全发现和审核状态，而不是客户端自报结论。

## 6. 故障注入

- 无效/缺失凭证：RunCase 必须为 `error`，证据为 `execution_outcome=error`，回调仍要完成。
- 超时：Activity 受测试计划 timeout 和 Temporal 上限约束，最终回写超时分类。
- 取消：调用 Run cancel 后 Workflow 取消保持幂等，Run 不得继续写成功结果。
- Worker 重启：Activity/Workflow 从 Temporal 历史恢复；嵌套 evidence 必须可反序列化。
- 控制面不可达：内部回调有限重试，不能连接业务数据库或生成假结果。

## 7. 回滚与清理

- 应用回滚：停止新 Worker，部署上一兼容版本；不要改写已经发布的迁移历史。
- 数据库迁移 `0018` 只新增证据/阶段字段和表；回滚前先导出 Run 证据，执行经批准的 Alembic downgrade。
- 取消未终止 Run，并确认 Temporal 无 Pending Activity。
- 删除临时测试会话和临时迁移数据库；保留正式 Run、Artifact、Finding、Review 与 Gate 审计记录。

## 8. 2026-07-11 本地验收记录

- PostgreSQL 空库升级与 `0017 -> 0018` 升级均到达 `0018`。
- Promptfoo 真实 CLI 假目标闭环通过，Finding 能触发人工审核与发布门禁阻断。
- 本地全栈 Run `96e345fb-936c-49f7-895c-9312709471c6` 已从 API、Temporal、Worker 回写到 PostgreSQL，终态为 `error`，统一证据已持久化。
- 真实 TapNow 画布当前没有项目凭证绑定；应用内浏览器访问目标被重定向到登录页。
- 同次 Run 的 Codex 探索还受到账号 usage limit 阻断。因此当前只能证明错误闭环正确，不能将真实目标成功执行标记为已验证。

