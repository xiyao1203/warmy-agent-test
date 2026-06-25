# ADR-0008: 开源依赖使用稳定版并锁定

- Status: Accepted
- Date: 2026-06-25

## Context

平台依赖前后端框架、浏览器、工作流和评测工具；浮动版本会造成不可复现构建和供应链风险。

## Decision

引入依赖时核对官方最新稳定版，并通过 Lockfile、Docker Tag 或固定 Commit 锁定。禁止使用 `latest`、Git `main` 和未固定引用。

## Consequences

- 构建可复现，升级变成显式任务。
- 引入和升级需记录许可证、安全、兼容性和回滚方案。
- Dependabot 只提出更新，不自动合并。

## Alternatives Considered

- 浮动范围或 `latest`：维护简单但不可复现。
- 永不升级：会积累安全和兼容性风险。

## Verification

- Lockfile 和容器 Tag 检查。
- CI 依赖审计与更新 PR。
