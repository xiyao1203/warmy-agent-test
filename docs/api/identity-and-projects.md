# Identity & Projects API

本文档描述 M1 平台基础阶段的身份认证、用户管理、项目隔离和审计 API。

完整 OpenAPI 规范见 `docs/api/openapi.json`，可通过 `make api-generate` 重新生成。

---

## 基础信息

| 项目 | 值 |
|---|---|
| Base URL | `http://localhost:8000/api/v1` |
| 认证方式 | 服务端 Session Cookie (`agenttest_session`) |
| CSRF 保护 | Cookie `agenttest_csrf` + Header `X-CSRF-Token` |
| 错误格式 | RFC 7807 Problem Details (`application/problem+json`) |

### 认证机制

- 登录成功后，服务端生成 32 字节随机 Session Token，仅将原始 Token 写入 HttpOnly + Secure + SameSite=Lax Cookie。
- 数据库只存储 Session Token 的 SHA-256 哈希，不存储明文。
- 所有写操作（POST/PATCH/DELETE）需要 CSRF Token：Cookie 中的 `agenttest_csrf` 值必须与 `X-CSRF-Token` 请求头匹配。
- 登录接口豁免 CSRF 检查。

### 错误响应

所有错误使用 RFC 7807 Problem Details 格式：

```json
{
  "title": "Authentication failed",
  "status": 401,
  "detail": "Invalid email or password"
}
```

---

## 1. 身份认证

### POST /auth/login

使用邮箱和密码登录，创建服务端 Session。

**请求体：**

```json
{
  "email": "admin@example.com",
  "password": "your-password"
}
```

**响应 200：**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "display_name": "Admin",
  "role": "super_admin",
  "status": "active",
  "must_change_password": false
}
```

**安全行为：**
- 设置 `agenttest_session` Cookie（HttpOnly, Secure, SameSite=Lax）。
- 设置 `agenttest_csrf` Cookie（Secure, SameSite=Lax，非 HttpOnly 以便前端读取）。
- 无论邮箱不存在还是密码错误，返回相同的 401 错误，不泄露账号是否存在。

**错误：**

| 状态码 | 说明 |
|---|---|
| 401 | 邮箱或密码不正确 |

### POST /auth/logout

撤销当前 Session 并清除 Cookie。

**要求：**
- 有效的 Session Cookie。
- `X-CSRF-Token` 请求头与 CSRF Cookie 匹配。

**响应 204：** 无内容，清除两个 Cookie。

**错误：**

| 状态码 | 说明 |
|---|---|
| 401 | 未登录 |
| 403 | CSRF 验证失败 |

### GET /auth/me

获取当前登录用户信息。

**响应 200：**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "display_name": "Admin",
  "role": "super_admin",
  "status": "active",
  "must_change_password": false
}
```

**错误：**

| 状态码 | 说明 |
|---|---|
| 401 | 未登录或 Session 已过期/被撤销 |

---

## 2. 用户管理

> 仅 `super_admin` 角色可访问。普通用户访问返回 403。

### GET /system/users

分页查询用户列表。

**查询参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `limit` | int | 每页数量（默认 20，最大 100） |
| `cursor` | UUID | 上一页返回的游标 |

**响应 200：**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "admin@example.com",
      "display_name": "Admin",
      "role": "super_admin",
      "status": "active",
      "must_change_password": false
    }
  ],
  "next_cursor": null
}
```

### POST /system/users

创建新用户。

**请求体：**

```json
{
  "email": "dev@example.com",
  "display_name": "Developer",
  "initial_password": "secure-password-123",
  "role": "developer"
}
```

**角色枚举：** `super_admin` | `developer` | `tester` | `reviewer` | `viewer`

**响应 201：** 返回创建的 UserResponse。

**安全行为：**
- 初始密码使用 Argon2id 哈希存储。
- 创建后自动记录审计日志。

### GET /system/users/{user_id}

查询单个用户详情。

**响应 200：** UserResponse。

### PATCH /system/users/{user_id}

更新用户信息（姓名、邮箱、角色）。

**请求体：**

```json
{
  "display_name": "Updated Name",
  "email": "new@example.com",
  "role": "tester"
}
```

**安全行为：**
- 不能降级最后一个活跃的超级管理员。
- 修改角色时自动记录审计日志。

### POST /system/users/{user_id}/reset-password

重置用户密码。

**请求体：**

```json
{
  "new_password": "new-secure-password-456"
}
```

**安全行为：**
- 撤销该用户所有现有 Session。
- 新密码使用 Argon2id 哈希。
- 记录审计日志（密码值脱敏）。

### POST /system/users/{user_id}/disable

禁用用户。

**安全行为：**
- 撤销该用户所有现有 Session。
- 不能禁用最后一个活跃的超级管理员。
- 当前登录的管理员不能禁用自己。
- 记录审计日志。

### POST /system/users/{user_id}/enable

启用已禁用的用户。

### DELETE /system/users/{user_id}

删除用户。

**安全行为：**
- 有历史活动的用户执行软删除（标记禁用），不物理删除。
- 不能删除最后一个活跃的超级管理员。
- 当前管理员不能删除自己。
- 撤销该用户所有 Session。

---

## 3. 项目管理

### GET /projects

查询当前用户可访问的项目列表。

- 超级管理员：返回所有项目。
- 普通用户：只返回已分配成员身份的项目。

**响应 200：**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Project A",
      "archived": false
    }
  ]
}
```

### POST /projects

创建新项目（仅超级管理员）。

**请求体：**

```json
{
  "name": "New Project",
  "key": "NEW-QA",
  "description": "Agent regression program",
  "lead_user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

创建者自动成为 `developer` 成员；指定的负责人若不是创建者，也会以 `developer` 身份加入项目。负责人始终必须是当前成员。

### GET /projects/{project_id}

查询项目详情。非成员访问返回 404（不泄露项目存在性）。

### PATCH /projects/{project_id}

更新项目名称、描述或负责人（仅超级管理员）。新负责人必须已经是项目成员。

**请求体：**

```json
{
  "name": "Renamed Project"
}
```

### POST /projects/{project_id}/archive

归档项目（仅超级管理员）。归档后项目不可创建新资源。

---

## 4. 项目成员

> 项目成员管理仅超级管理员可操作。普通成员可查看所属项目的成员列表。

### GET /projects/{project_id}/members

查询项目成员列表。非成员访问返回 404。

**响应 200：**

```json
{
  "items": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "developer"
    }
  ]
}
```

**成员角色枚举：** `developer` | `tester` | `reviewer` | `viewer`

### POST /projects/{project_id}/members

添加项目成员（仅超级管理员）。

**请求体：**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "developer"
}
```

### PATCH /projects/{project_id}/members/{user_id}

修改成员角色（仅超级管理员）。

**请求体：**

```json
{
  "role": "reviewer"
}
```

### DELETE /projects/{project_id}/members/{user_id}

移除项目成员（仅超级管理员）。

**安全行为：** 移除后该用户立即失去项目访问权限；当前项目负责人不能被移除，必须先把负责人变更为另一名现有成员。

---

## 5. 审计

### GET /system/audit

查询全局审计日志（仅超级管理员）。

**查询参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `limit` | int | 每页数量 |
| `cursor` | string | 游标 |

**响应 200：**

```json
{
  "items": [
    {
      "id": "audit-entry-id",
      "action": "identity.login.succeeded",
      "actor_user_id": "550e8400-e29b-41d4-a716-446655440000",
      "object_type": "user",
      "object_id": "550e8400-e29b-41d4-a716-446655440000",
      "project_id": null,
      "changes": {},
      "source_ip": null,
      "created_at": "2026-06-25T10:00:00Z"
    }
  ]
}
```

### GET /projects/{project_id}/audit

查询项目审计日志（项目成员可访问，非成员返回 404）。

---

## 6. 健康检查

### GET /health

```json
{
  "service": "control-api",
  "status": "ok",
  "version": "0.1.0"
}
```

---

## 审计事件清单

| 事件 | 触发条件 |
|---|---|
| `identity.login.succeeded` | 用户登录成功 |
| `identity.login.failed` | 用户登录失败 |
| `identity.user.created` | 管理员创建用户 |
| `identity.user.updated` | 管理员编辑用户 |
| `identity.user.reset_password` | 管理员重置密码 |
| `identity.user.disabled` | 管理员禁用用户 |
| `identity.user.enabled` | 管理员启用用户 |
| `identity.user.deleted` | 管理员删除用户 |
| `projects.created` | 创建项目 |
| `projects.renamed` | 重命名项目 |
| `projects.archived` | 归档项目 |
| `projects.member.added` | 添加成员 |
| `projects.member.updated` | 修改成员角色 |
| `projects.member.removed` | 移除成员 |

所有审计记录中的密码、Token、Cookie 等敏感字段自动脱敏。
