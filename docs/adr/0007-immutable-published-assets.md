# ADR-0007: 已发布测试资产版本不可变

- Status: Accepted
- Date: 2026-06-25

## Context

测试运行必须可复现；如果已发布版本被原地修改，历史结果将失去解释依据。

## Decision

已发布的 AgentVersion、DatasetVersion、TestCaseVersion 和 TestPlanVersion 不可修改。编辑已发布资产时创建新版本，Run 始终引用确切版本。

## Consequences

- 历史运行可重现和审计。
- 版本数据量增加，需要归档与索引策略。
- “最新版本”不能作为 Run 的持久化引用。

## Alternatives Considered

- 原地更新：实现简单但破坏复现性。
- 仅保存变更日志：恢复任意历史状态复杂且脆弱。

## Verification

- 发布后更新被拒绝的领域测试。
- Run 外键与版本快照契约测试。
