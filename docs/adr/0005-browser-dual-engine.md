# ADR-0005: 浏览器测试采用双引擎

- Status: Accepted
- Date: 2026-06-25

## Context

稳定回归和探索式路径发现的目标不同，单一浏览器工具难以同时优化确定性与探索能力。

## Decision

Playwright 用于确定性关键链路回归与证据采集；Browser Harness 用于探索测试、路径发现和修复候选。探索结果必须审核后才能进入回归集。

## Consequences

- 两类 Runner 使用独立队列和资源限制。
- 证据格式通过统一 Artifact 契约汇总。
- 探索模式不替代稳定发布门禁。

## Alternatives Considered

- 仅 Playwright：探索和自适应能力不足。
- 仅 Browser Harness：确定性和可重复性不足。

## Verification

- Playwright E2E 与 Browser Harness 审核流程测试。
- 运行结果保存截图、录像、网络和 Trace。
