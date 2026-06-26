# Runs API

M3 首个纵向切片新增项目隔离的运行 API。

## 创建运行

```http
POST /api/v1/projects/{project_id}/runs
Idempotency-Key: release-20260626-001
X-CSRF-Token: <csrf>
```

请求体：

```json
{
  "test_plan_version_id": "uuid"
}
```

约束：

- `Idempotency-Key` 必填，且在同一项目内唯一。
- `test_plan_version_id` 必须是当前项目下已发布的测试计划版本。
- 测试计划引用的 AgentVersion 和 DatasetVersion 必须是已发布版本。
- 当前切片只创建 API 模式 RunCase。

响应为 `RunResponse`。首次创建返回 `201`，重复幂等键返回同一 Run。

## 查询运行

```http
GET /api/v1/projects/{project_id}/runs
GET /api/v1/projects/{project_id}/runs/{run_id}
GET /api/v1/projects/{project_id}/runs/{run_id}/cases
```

所有查询都校验项目成员关系；跨项目访问返回 404。

## 取消运行

```http
POST /api/v1/projects/{project_id}/runs/{run_id}/cancel
X-CSRF-Token: <csrf>
```

只有项目编辑角色可取消。终态 Run 不允许再次取消。

## 实时事件

```http
GET /api/v1/projects/{project_id}/runs/{run_id}/events
```

当前切片提供 SSE 快照事件 `run.snapshot`；后续任务会扩展为 RunEvent 增量流。

## 内部结果回写

```http
POST /api/v1/projects/{project_id}/runs/{run_id}/result
X-Internal-Token: <internal-token>
```

该端点只供受控 Worker/Workflow 回写执行结果，浏览器前端不得调用。请求体：

```json
{
  "cases": [
    {
      "run_case_id": "uuid",
      "status": "passed",
      "output": { "answer": "hello world" },
      "trace": [{ "name": "http.request", "status": "ok" }],
      "duration_ms": 42
    }
  ]
}
```

控制面会校验项目与 Run，按 RunCase 更新结果和 Trace，并聚合 Run 终态。已进入终态的 Run 再收到相同回写时保持幂等，不覆盖结果。

## 状态语义

- `passed`：全部 RunCase 通过。
- `failed`：至少一个确定性断言失败，没有平台错误。
- `error`：执行器、目标产品或平台出现错误。
- `cancelled`：用户取消或运行被取消。

`failed`、`error` 和 `cancelled` 不可混用。
