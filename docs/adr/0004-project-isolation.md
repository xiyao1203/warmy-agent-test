# ADR-0004: 项目数据由后端强制隔离

- Status: Accepted
- Date: 2026-06-25

## Context

平台采用项目内共享、项目间隔离；前端隐藏入口无法防止直接 API、搜索、导出或文件访问。

## Decision

所有项目业务数据直接或可验证地关联 `project_id`。Repository 查询必须接收项目上下文，后端依次校验身份、系统角色、成员关系、资源项目和操作权限。无权访问其他项目时返回 404。

## Consequences

- 唯一约束和高频索引优先包含 `project_id`。
- 禁止仅按资源 ID 查询项目资源。
- 对象存储路径前缀不能替代授权。

## Alternatives Considered

- 仅前端控制：不能形成安全边界。
- 仅 PostgreSQL RLS：可作纵深防御，但不能替代应用 Policy。

## Verification

- 项目 Policy、API 契约和 PostgreSQL 隔离测试。
- 架构评审检查项目 Repository 方法。
