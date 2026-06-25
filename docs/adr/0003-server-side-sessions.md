# ADR-0003: 浏览器认证使用服务端 Session

- Status: Accepted
- Date: 2026-06-25

## Context

用户禁用、密码重置和主动注销后必须立即撤销会话，长期不可撤销 JWT 不适合作为浏览器主会话。

## Decision

浏览器使用服务端可撤销 Session。浏览器仅保存随机 Token 的 Secure、HttpOnly、SameSite Cookie；数据库只保存 Token Hash、过期时间和撤销时间。密码使用 Argon2id，写请求使用 CSRF 防护。

## Consequences

- 用户状态变化可以立即撤销 Session。
- Session 存储和查询成为登录请求依赖。
- 原始 Token、密码和 Cookie 不得写入日志或审计。

## Alternatives Considered

- 长期 JWT：撤销与权限即时失效复杂。
- Token 明文入库：数据库泄露风险不可接受。

## Verification

- 身份认证单元与契约测试。
- Session Hash、Cookie 属性和 CSRF 测试。
