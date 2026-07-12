# Run 可信闭环运维手册

## 1. 运行边界

- Run 终态结果是事实源；后处理失败不得修改或回滚 Run 终态。
- 管线版本为 `trust-loop-v1`，稳定 Workflow ID 为 `run-trust-loop-{run_id}-trust-loop-v1`。
- 阶段固定为 `classify、diagnose、reproduce、calibrate、evaluate_gate、finalize`。
- Worker 只调用带 `X-Internal-Token` 的 Control API，不连接业务数据库；日志、Evidence 和 Workflow History 禁止包含凭证、Cookie 或原始 Auth State。

## 2. 健康检查与验收

确认 PostgreSQL、Temporal、Control API、API Runner 和被测目标均可用，并确保 Control API 与 Worker 使用相同的 `AGENTTEST_INTERNAL_API_TOKEN`、Temporal namespace 和 task queue。

```bash
curl -f http://127.0.0.1:8181/api/v1/health
uv run pytest workers/api-runner/tests/test_postprocess_workflow.py -q
make trust-loop-acceptance
```

公共路径矩阵覆盖成功、产品错误、协议错误、鉴权失效、额度不足、超时、瞬态恢复、Evidence 缺失和提示注入。生产验证不得用 Fake Target 代替真实外部目标验收。

## 3. Pending 任务恢复

1. 按 `project_id、run_id、pipeline_version` 查询 `run_postprocess_jobs`，确认 Run 已终态且任务处于 `pending` 或非终态。
2. 检查 Temporal 中稳定 Workflow ID。Workflow 存在时恢复或重启 API Runner，由 Temporal 重放；不得创建随机 Workflow ID。
3. Workflow 不存在时，使用应用层 `PostprocessScheduler` 重新调度同一任务。唯一约束和阶段幂等键会复用已有记录。
4. 对照 `run_postprocess_stage_results` 定位最后完成阶段。不得手工跳过阶段、直接写终态或修改 Evidence。
5. 恢复后通过项目公开 API确认任务终态及五类投影，不能只查看 Temporal 状态。

## 4. 版本混用与降级

- Worker 无法识别管线版本、阶段枚举或内部响应字段时，先停止新 Worker 发布并恢复与 Control API 同一版本的镜像。
- 模型服务不可用时诊断阶段应以 warning 和 `inconclusive` 完成；不得反复重试模型而阻塞确定性门禁。
- 无复现器、复现不一致或次数不足的候选进入 Quarantine，由人工复核；不得手工改为 `published`。
- Evidence 缺失、执行失败或安全阻断必须 fail closed。质量高分不能覆盖这些结果。

## 5. 安全停用新调度

紧急情况下先在 Control API 部署中关闭后处理调度入口或回退到未启用调度的兼容版本，再排空已启动 Workflow。不要删除已有任务、阶段结果或 Run 数据。恢复时仍使用相同管线版本和稳定 Workflow ID，让幂等约束接管重复请求。

## 6. 数据库迁移与回滚

- `0022` 创建可信闭环持久化表；`0023` 将 `audit.audit_logs` 对齐到 ORM 使用的 `public.audit_logs`；`0024` 补齐 `runs.session_id`。
- 上线前执行空库 `upgrade head` 和上一版本升级，并验证 `public.audit_logs`、`runs.session_id`、项目复合外键、唯一约束和索引。
- `0024` 只删除可空 `runs.session_id`，降级前确认旧应用不再写入该列。
- `0023` 降级会把审计表移回 `audit` schema，必须与使用该 schema 的旧应用同时切换。
- 降到 `0021` 会删除全部可信闭环记录。仅在已停止调度、完成备份且明确接受数据丢失时执行，常规回滚应保留 `0022` 及后续数据。

## 7. 故障分类

- `target_product_error`、`target_protocol_error`：确定性目标失败，不由 Temporal 重试。
- `auth_expired`、`quota_exceeded`：环境失败；修复登录态或额度后重跑，不修改历史事实。
- `network_unavailable`：网络、5xx 或超时耗尽重试后的稳定错误类型。
- 内部 API 403：核对令牌配置，不打印令牌值。
- 阶段 409：通常表示乱序或重复版本调用，检查 Workflow/Control API 版本和阶段回执。
