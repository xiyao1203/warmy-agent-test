# Temporal Python SDK 依赖核对

- 核对日期：2026-06-26
- 官方包：`temporalio`
- 锁定版本：`1.29.0`
- 官方仓库：`temporalio/sdk-python`
- 许可证：MIT
- Python 兼容：项目使用 Python 3.12，处于 SDK 支持范围。
- 用途：M3 运行工作流、Activity、重试、超时、取消与 replay。
- 权限与网络：Worker 连接 Temporal Server；SDK 本身不应访问业务数据库。
- 数据边界：Workflow/Activity 载荷只包含运行所需的不可变快照和短期凭证。
- 升级验证：Control API 契约、Workflow replay、Activity Mock、重试、超时、取消和 100 用例批量测试。
- 回滚：恢复 `pyproject.toml` 与 `uv.lock` 中上一锁定版本，并重放已有 Workflow History。
- 替代方案：Celery/RQ 不满足本项目长流程恢复、Signal、取消和 replay 要求，已由 ADR-0002 排除。

