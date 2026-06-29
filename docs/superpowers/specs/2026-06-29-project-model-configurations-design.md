# 项目级大模型配置与真实调用设计

## 1. 目标与范围

平台新增项目级大模型配置。项目成员可配置 OpenAI-Compatible 服务，并为测试 Agent 对话、文本裁判、视觉裁判分别选择默认模型。测试 Agent 和模型裁判只产生真实模型响应；缺少配置、凭证无效、上游失败或模型输出不合法时返回明确错误，禁止 Mock、静态占位结果和环境变量 API Key 兜底。

首期只实现 OpenAI-Compatible `chat/completions` 协议，不实现 Anthropic、Gemini 等原生协议。配置在项目内共享、项目间隔离。

## 2. 方案选择

采用独立 `model_configs` 业务模块和独立 Model Runner Worker。没有复用环境模板或评分器 JSON，因为模型凭证有独立权限、不变量、默认用途、连接验证和运行快照要求；也没有建立全局供应商目录，因为首期只有一种兼容协议，过早抽象会增加维护成本。

## 3. 领域模型

### 3.1 ModelConfiguration

- `id`、`project_id`、`name`
- `provider_type`：首期固定为 `openai_compatible`
- `base_url`：供应商 API 根地址，保存规范化 URL
- `model_name`
- `encrypted_api_key`：仅持久化层和运行快照使用，普通 API 永不返回
- `api_key_hint`：只保存尾部最多四位的脱敏提示
- `supports_text`、`supports_vision`
- `enabled`
- `created_by`、`created_at`、`updated_at`

同一项目内名称唯一。配置必须至少支持文本；视觉默认模型必须声明视觉能力。停用配置不能作为默认模型或发起调用。

### 3.2 ProjectModelDefault

用途枚举固定为：

- `test_agent_chat`
- `text_judge`
- `vision_judge`

每个项目每种用途最多一条默认配置。删除或停用仍被默认用途引用的模型前，必须先重新分配默认模型。

## 4. 安全与网络

部署通过 `AGENTTEST_MODEL_CREDENTIAL_KEY` 提供 32 字节主密钥。Control API 只负责在写入时使用 AES-256-GCM 加密，不在普通请求中解密。密文携带随机 nonce 和版本号，便于后续密钥轮换。

调用时 Control API 将最小不可变配置快照和密文通过 Temporal 发送给 Model Runner。Worker 在 Activity 生命周期内解密，调用结束立即丢弃明文。日志、错误、Trace、OpenAPI 和前端状态均不得包含密钥或完整 Authorization。

`base_url` 只允许 HTTP/HTTPS。生产环境要求 HTTPS；本地与测试环境只允许回环地址使用 HTTP。解析后的目标禁止私网、链路本地、元数据地址和 DNS 重绑定；Worker 出站前再次校验。

## 5. 调用架构与数据流

```text
Web → Control API → 项目权限与默认模型解析
    → 加密配置快照 → Temporal ModelInvocationWorkflow
    → Model Runner Activity 解密 → OpenAI-Compatible API
    → 结构化结果 → Control API 校验并返回/持久化
```

Model Runner 使用 `POST {base_url}/chat/completions`，显式设置连接/读取总超时。连接测试发送最小文本请求；视觉模型配置可发送一张内嵌的一像素测试图验证视觉输入能力。

错误分类：配置错误和模型输出不合法为 `ValidationError`；401/403 为 `PermissionError`；408/429/5xx 和网络超时为 `TransientError`；其他上游协议错误为 `PlatformError`。任何错误都不生成替代业务结果。

## 6. 测试 Agent 与裁判接入

测试 Agent 的聊天请求按 `project_id` 解析 `test_agent_chat` 默认模型，将当前用户消息和必要的会话上下文发送给 Worker，并要求返回符合 Pydantic Schema 的 JSON 测试计划。Control API 校验结构后写入会话；无默认模型返回 409，模型不可用返回 502/503，输出不合法返回 422。

文本裁判和视觉裁判分别解析 `text_judge`、`vision_judge` 默认模型。评分结果记录模型配置 ID、供应商、模型名、调用时间、Token/延迟和评分 Prompt 版本，不保存密钥。视觉裁判拒绝不具备视觉能力的配置。

## 7. API

- `GET /api/v1/projects/{project_id}/model-configs`
- `POST /api/v1/projects/{project_id}/model-configs`
- `GET /api/v1/projects/{project_id}/model-configs/{model_config_id}`
- `PATCH /api/v1/projects/{project_id}/model-configs/{model_config_id}`
- `DELETE /api/v1/projects/{project_id}/model-configs/{model_config_id}`
- `POST /api/v1/projects/{project_id}/model-configs/{model_config_id}/test-connection`
- `GET /api/v1/projects/{project_id}/model-defaults`
- `PUT /api/v1/projects/{project_id}/model-defaults/{purpose}`

读取接口对项目成员开放但只返回 `has_api_key` 和 `api_key_hint`。创建、编辑、删除、连接测试和修改默认值要求项目写权限及 CSRF。跨项目资源统一返回 404。

## 8. 前端体验

在项目导航增加“模型配置”，页面沿用现有高密度列表和 Dialog 表单。顶部展示三张默认用途卡；下方展示模型名称、协议、模型 ID、服务域名、能力、启停状态和默认用途标签。

创建/编辑表单包含名称、Base URL、模型 ID、API Key、文本/视觉能力和启用状态。API Key 为写入专用字段，编辑时留空表示保留；页面不提供查看或复制明文。连接测试必须由用户明确点击，并展示成功延迟或可修复的错误。页面覆盖加载、空、错误、无权限、提交中、冲突和删除受阻状态。

测试 Agent 页面在缺少默认模型时展示前往模型配置的明确入口，上游错误就近展示，不能伪装成 Assistant 消息。

## 9. 数据库与兼容性

新增 `model_configurations` 和 `project_model_defaults` 两张表，外键均关联项目，唯一约束分别为 `(project_id, name)` 和 `(project_id, purpose)`；默认表使用 `(project_id, model_config_id)` 外键保证项目一致性。迁移支持空库和上一版本升级，降级只删除新增表。

运行时不读取 `OPENAI_API_KEY`、`CANVAS_MODEL_API_KEY` 等模型 API Key 环境变量。现有 Mock LLM 和占位 OpenAI Adapter 删除。部署级 `AGENTTEST_MODEL_CREDENTIAL_KEY` 只用于加密项目密钥，不代表任何模型供应商凭证。

## 10. 验收与测试

- 领域测试覆盖名称、URL、能力、启停与默认用途不变量。
- Repository/迁移测试覆盖项目隔离、唯一约束、外键、空库和升级。
- API 契约测试覆盖认证、CSRF、角色、跨项目 404、密钥不回显和错误契约。
- Worker 使用本地 Fake HTTP 服务验证真实 OpenAI-Compatible 请求、超时、401、429、5xx、无效 JSON、文本和视觉消息。
- 测试 Agent 验证无默认模型明确失败、配置后真实调用、结构校验和无 Mock 兜底。
- 前端组件和关键 E2E 覆盖配置 CRUD、默认模型、连接测试、空/错/权限状态和缺少模型引导。
- 执行格式、Lint、类型检查、后端/Worker/前端测试、OpenAPI 生成和生产构建，并扫描 Mock、占位注释和密钥泄漏。

## 11. 明确不做

- 不做供应商原生协议、价格目录、自动模型发现或模型市场。
- 不允许在浏览器保存 API Key。
- 不以内存会话、静态结果、随机分数或 Mock 作为运行回退。
- 不在本任务重构无关运行、评分器或页面模块。
