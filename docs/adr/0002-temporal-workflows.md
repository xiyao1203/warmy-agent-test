# ADR-0002: 长任务统一使用 Temporal

- Status: Accepted
- Date: 2026-06-25

## Context

测试运行涉及长时间执行、重试、取消、人工等待和断点恢复，普通后台任务队列不足以表达可靠状态机。

## Decision

长任务统一由 Temporal Workflow 编排；浏览器、API、评测和安全操作由独立 Worker Activity 执行。

## Consequences

- Workflow 必须可重放，只负责编排。
- Activity 明确超时、重试、取消和幂等策略。
- 核心业务不混用第二套长任务系统。

## Alternatives Considered

- Celery/RQ：恢复和状态编排能力不足。
- 控制面进程内任务：不可可靠恢复且难以隔离资源。

## Verification

- 技术架构规范第 4.2、7.6、10 章。
- Worker 阶段验证 replay、retry、cancel 和 idempotency。
