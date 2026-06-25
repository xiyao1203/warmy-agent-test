# ADR-0006: 领域扩展通过公开 Plugin SDK

- Status: Accepted
- Date: 2026-06-25

## Context

平台需要支持画布、HTTP、浏览器及后续多类 Agent，核心流程不能持续增加按 Agent 类型分支。

## Decision

不同 Agent 产品通过 Adapter、Artifact 和 Scorer 插件扩展。插件只能依赖公开 Plugin SDK 和版本化契约，不得导入平台内部模块。

## Consequences

- 通用核心保持领域无关。
- SDK 需要兼容策略、契约测试和版本管理。
- 画布 Agent 是首个插件，不成为核心模型特例。

## Alternatives Considered

- 核心增加 `if agent_type`：长期导致耦合和回归风险。
- 插件直接调用内部服务：无法维持兼容边界。

## Verification

- 插件契约和兼容性测试。
- 架构检查禁止插件导入平台内部路径。
