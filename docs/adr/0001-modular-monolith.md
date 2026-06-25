# ADR-0001: 控制面采用模块化单体

- Status: Accepted
- Date: 2026-06-25

## Context

MVP 业务边界仍在演进，过早拆分微服务会增加事务、部署、契约版本和运维成本。

## Decision

FastAPI 控制面采用模块化单体，按业务模块组织 Domain、Application、Infrastructure 和 API。模块之间只通过公开 Application 接口、`public.py` 或领域事件协作。

## Consequences

- 保持单部署单元和本地事务能力。
- Domain 不依赖框架，API 不直接访问 ORM。
- 当模块形成独立扩缩容、发布或团队边界时再评估拆分。

## Alternatives Considered

- 按技术层组织的大型单体：边界容易退化。
- MVP 直接拆微服务：协调和运维成本过高。

## Verification

- `scripts/check_architecture.py`
- `apps/control-api/tests/architecture/test_module_boundaries.py`
