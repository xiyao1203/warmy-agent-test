# Worker 开发规则

本目录继承根 `AGENTS.md`，并追加以下约束：

- Temporal Workflow 只编排，不执行网络、文件、数据库、当前时间或随机操作。
- 所有外部 I/O 必须位于 Activity 或 Adapter。
- Worker 不导入 `apps/control-api` 内部模块，不持有业务数据库连接。
- Activity 必须显式设置超时、重试策略；长任务发送 Heartbeat 并响应取消。
- 非幂等外部操作必须携带业务幂等键。
- 任务载荷使用本 Worker 的公开 DTO，只包含当前运行所需最小快照。
- 日志、Trace、请求和响应必须脱敏 Authorization、Cookie、Token 和 API Key。
- 新增行为先覆盖 Fake Target、重试、超时、取消、错误分类和 Workflow replay 测试。

