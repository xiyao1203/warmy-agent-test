# Test Assets API

本文档描述 M2 测试资产阶段的 Agent、Dataset、TestPlan 和
EnvironmentTemplate API。完整契约以 `docs/api/openapi.json` 为准。

## 通用规则

| 项目 | 规则 |
|---|---|
| Base URL | `http://localhost:8000/api/v1` |
| 认证 | 服务端 Session Cookie `agenttest_session` |
| 写操作 | 同时提交 Cookie `agenttest_csrf` 与 Header `X-CSRF-Token` |
| 项目隔离 | 非项目成员访问项目资源统一返回 404 |
| 写权限 | `super_admin`、`developer`、`tester` |
| 只读权限 | `reviewer`、`viewer` |
| 错误格式 | RFC 7807 Problem Details |

列表接口使用 `limit` 和 `cursor` 游标分页。资源路径中的父级 ID 与实际归属
不一致时返回 404，避免跨项目或跨聚合读取。

## Agent

```text
GET    /projects/{project_id}/agents
POST   /projects/{project_id}/agents
GET    /projects/{project_id}/agents/{agent_id}
PATCH  /projects/{project_id}/agents/{agent_id}
GET    /projects/{project_id}/agents/{agent_id}/versions
POST   /projects/{project_id}/agents/{agent_id}/versions
GET    /projects/{project_id}/agents/{agent_id}/versions/{version_id}
PATCH  /projects/{project_id}/agents/{agent_id}/versions/{version_id}
POST   /projects/{project_id}/agents/{agent_id}/versions/{version_id}/publish
```

Agent 类型为 `generic_http` 或 `canvas`。版本配置包含 API 地址、模型参数、
系统提示词、工具、超时和成本限制。版本发布后不可修改，需创建新版本继续编辑。

## Dataset 与 TestCase

```text
GET    /projects/{project_id}/datasets
POST   /projects/{project_id}/datasets
GET    /projects/{project_id}/datasets/{dataset_id}
PATCH  /projects/{project_id}/datasets/{dataset_id}
GET    /projects/{project_id}/datasets/{dataset_id}/versions
POST   /projects/{project_id}/datasets/{dataset_id}/versions
GET    /projects/{project_id}/datasets/{dataset_id}/versions/{version_id}
POST   /projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/publish
GET    /projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/cases
POST   /projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/cases
PATCH  /projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/cases/{case_id}
DELETE /projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/cases/{case_id}
POST   /projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/import
GET    /projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/export
```

TestCase 支持 `api` 和 `browser` 执行模式，并可配置断言、评分器、初始状态、
期望结果、安全策略、标签和风险等级。已发布的数据集版本只读。

导入支持 `json`、`jsonl`、`csv`，请求体包含 `format` 和 `content`。导入采用
全有或全无语义，失败响应中的 `errors` 提供行号和原因。导出通过 `format`
查询参数选择相同的三种格式。

## TestPlan

```text
GET    /projects/{project_id}/test-plans
POST   /projects/{project_id}/test-plans
GET    /projects/{project_id}/test-plans/{plan_id}
PATCH  /projects/{project_id}/test-plans/{plan_id}
GET    /projects/{project_id}/test-plans/{plan_id}/versions
POST   /projects/{project_id}/test-plans/{plan_id}/versions
GET    /projects/{project_id}/test-plans/{plan_id}/versions/{version_id}
PATCH  /projects/{project_id}/test-plans/{plan_id}/versions/{version_id}
POST   /projects/{project_id}/test-plans/{plan_id}/versions/{version_id}/publish
```

版本可引用 AgentVersion、DatasetVersion 和 EnvironmentTemplate，并配置运行
次数、并发、超时、重试、评分器、通过阈值和成本预算。已发布版本不可修改。

## EnvironmentTemplate

```text
GET    /projects/{project_id}/environment-templates
POST   /projects/{project_id}/environment-templates
GET    /projects/{project_id}/environment-templates/{template_id}
PATCH  /projects/{project_id}/environment-templates/{template_id}
DELETE /projects/{project_id}/environment-templates/{template_id}
```

模板类型为 `blank` 或 `preset`，配置字段保存测试执行所需的 JSON 环境状态。

## 常见错误

| 状态码 | 含义 |
|---|---|
| 400 | 请求字段或导入内容无效 |
| 401 | 未登录或 Session 无效 |
| 403 | CSRF 校验失败或没有项目写权限 |
| 404 | 项目、资源或父子路径不存在 |
| 409 | 尝试修改已发布的不可变版本 |

## 生成与校验

```bash
make api-generate
make api-check
```

TypeScript 客户端位于 `packages/generated-api-client`，前端应通过该包访问 API，
不得复制生成类型或手写重复契约。
