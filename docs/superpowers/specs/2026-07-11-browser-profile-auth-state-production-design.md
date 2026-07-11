# 浏览器实例登录态生产执行闭环设计

日期：2026-07-11  
状态：已确认
关联任务：TASK-20260711-002  
关联需求：PRD 3.1、3.2、7.1、7.3、8.7、8.8、10、11、15  
关联架构：技术架构 8、9、10、12、13、14、15、21

## 1. 目标

让平台中“用已登录浏览器”从配置选项变成可用于 CI、Worker 重启和分布式执行的生产能力：用户只需在浏览器实例中完成一次登录，浏览器停止后，后续 Run 仍可在隔离上下文中恢复登录态，真实操作目标 Agent 产品并采集可审计证据。

本阶段完成后，平台必须满足：

- Agent 版本只引用 `browser_profile_id`，不保存 Cookie、Token、密码或宿主机路径。
- 浏览器实例登录完成后导出 Cookie、LocalStorage 和 IndexedDB，使用平台主密钥加密持久化。
- Worker 仅在指定项目、Run、RunCase 和浏览器实例范围内，通过短期租约获得登录态。
- TapNow 正式执行复用登录态，不再无条件启动无状态浏览器并重复登录。
- 真实执行保存截图、录像、Playwright Trace、网络摘要、控制台错误和 Canvas 结构。
- 登录过期、待人工确认、目标额度不足、平台错误和目标产品错误具有不同分类，不得假通过。
- 浏览器实例停止、Worker 重启和并发 RunCase 不破坏登录态或互相污染。

## 2. 方案选择

### 2.0 参考实现与取舍

本设计参考 `xiyao1203/runtest` 在提交 `ac0bfd4d0a81952e05aae837c336b724ade62a7c` 中的浏览器实例实现，吸收以下经过实际工程验证的模式：

- 浏览器实例是项目级资源，并具有 `draft/initializing/ready/expired/disabled` 等明确生命周期。
- 交互式初始化使用独立 `user_data_dir` 启动 Chromium，通过仅绑定 `127.0.0.1` 的 CDP 端点连接。
- 用户确认登录完成后，通过 Playwright `connect_over_cdp` 从活动上下文导出 Storage State，再终止初始化浏览器进程。
- 执行前对实例加排他锁，终态、异常、进程失效和超时路径均释放锁；临时目录和持久目录采用不同清理策略。
- CDP 启动等待、进程存活探测、陈旧 Singleton 文件清理和失败分类作为浏览器运行时可靠性基线。

不直接复制参考项目的本机明文路径模型。AgentTest 是多项目、分布式生产平台，因此改为数据库保存元数据、加密保存 Storage State、Worker 通过短期作用域租约取用；用户 API 不暴露宿主机路径、CDP 地址和 Cookie 信息。参考项目中“资料目录存在即可能可用”的判断也不作为登录成功依据，必须同时通过快照导出、目标域状态校验和独立上下文验证。

### 2.1 采用：加密 Storage State 快照 + 短期运行租约

浏览器实例用于交互式登录和维护身份；`login-complete` 通过 CDP 从浏览器上下文导出 Playwright Storage State，将 JSON 序列化后加密保存。运行时 Worker 通过内部租约接口获取明文状态，仅在 Activity 内存中短暂存在，并传入新建的隔离 BrowserContext。

此方案支持浏览器实例停止后执行、Worker 横向扩容、重启恢复和 CI/CD，不依赖共享宿主机目录。

### 2.2 不采用：只连接运行中的 CDP

该方案能保留 SessionStorage 等进程内状态，但要求浏览器实例长期运行，跨主机和容器路由复杂，无法满足稳定 CI。后续仅可作为明确配置的兼容模式，不作为本阶段默认路径。

### 2.3 不采用：Worker 挂载浏览器 User Data Directory

共享用户目录存在并发损坏、文件锁、跨主机不可用和凭证泄漏风险，禁止作为生产执行方案。

## 3. 架构边界

### 3.1 Control API

负责浏览器实例元数据、项目权限、登录态加密持久化、租约授权、运行归属校验和审计。用户 API 永不返回登录态明文、加密信封或对象存储内部地址。

### 3.2 Browser Profile Runtime

负责启动带独立 `user_data_dir` 的交互式 Chromium、提供受控 CDP 端点、在用户确认完成登录后导出 Storage State，以及停止浏览器进程。运行进程表属于运行时状态，不作为业务事实源。

### 3.3 Temporal Workflow

只传递 `browser_profile_id`、登录策略、目标 URL、运行 ID 和短期内部调用上下文。Workflow 历史禁止出现 Storage State、Cookie、密码或解密后的凭证。

### 3.4 API Runner

在 Activity 内兑换登录态、创建隔离 BrowserContext、执行目标产品操作、采集证据、上传 Artifact 并清除内存和临时目录。Worker 不连接业务数据库。

### 3.5 Canvas Plugin

只负责 TapNow 页面契约：认证状态判断、输入、提交、执行状态、待确认状态、Canvas 提取和危险动作阻断。插件不读取平台 ORM、凭证仓库或运行数据库。

## 4. 数据模型

新增 Alembic 迁移 `0019_browser_profile_auth_state`。

### 4.1 `browser_profiles`

- `id UUID`：浏览器实例 ID。
- `project_id UUID`：强制项目隔离并建立外键。
- `name`、`target_domain`：用户可见元数据。
- `user_data_dir`、`cdp_port`：本地 Browser Runtime 配置；用户 API仅返回必要的可见信息。
- `status`：`stopped/running/error`，启动后可由运行时状态校正。
- `last_login_at`、`last_verified_at`：登录和最近验证时间。
- `auth_state_envelope TEXT NULL`：加密后的 Storage State。
- `auth_state_sha256 CHAR(64) NULL`：明文规范化 JSON 的摘要，用于一致性验证，不可反推出登录态。
- `auth_state_version INTEGER`：快照格式版本。
- `auth_state_updated_at`：快照更新时间。
- `created_by`、`created_at`、`updated_at`。
- 唯一约束：`project_id + name`。
- 索引：`project_id + updated_at`、`project_id + status`。

### 4.2 旧 JSON 注册表迁移

数据库成为浏览器实例事实源。提供显式、幂等的一次性导入命令，将 `~/.agenttest/browser-profiles/{project_id}.json` 的元数据写入数据库；导入不复制 Cookie 文件，不在 GET 请求或应用启动时隐式写库。导入成功后旧 JSON 仅作为回滚备份，API 不再双写。

### 4.3 登录态加密

复用平台凭证 Envelope Encryption 主密钥和版本化信封格式，但使用独立 AAD：

```text
agenttest:browser-auth-state:v1:{project_id}:{browser_profile_id}
```

不同项目或浏览器实例之间的信封不可互换。轮换密钥时提供重新加密服务，不修改业务 ID。

## 5. API 契约

### 5.1 用户 API

- 现有浏览器实例 CRUD 改为数据库仓储。
- `POST .../browser-profiles/{profile_id}/start`：启动交互式浏览器。
- `POST .../browser-profiles/{profile_id}/login-complete`：
  1. 校验用户为项目 Editor 以上；
  2. 连接该实例 CDP；
  3. 导出包含 IndexedDB 的 Storage State；
  4. 校验至少存在与目标域关联的 Cookie 或 Origin 状态；
  5. 加密并持久化；
  6. 更新登录时间和审计记录；
  7. 根据 `stop_after_save` 停止浏览器。
- `POST .../browser-profiles/{profile_id}/verify`：使用临时隔离上下文加载快照并访问目标 URL，只判断认证状态，不执行 Agent 指令。

Profile 响应新增：

- `auth_state_status=missing/ready/expired/error`
- `auth_state_updated_at`
- `last_verified_at`

不得返回 `auth_state_envelope`、Cookie 数量、Cookie 名称或 Token 细节。

### 5.2 Worker 内部 API

新增：

```text
POST /api/v1/internal/projects/{project_id}/browser-session-leases:redeem
```

请求包含：`run_id`、`run_case_id`、`browser_profile_id`。控制面必须验证：

- 内部 Token 正确；
- Run 属于该项目且处于可执行状态；
- RunCase 属于该 Run；
- 不可变运行快照确实引用该浏览器实例；
- 浏览器实例属于同一项目且存在可用登录态。

响应包含 `storage_state` 和格式版本，不包含数据库字段、主密钥或加密信封。租约仅供当前 Activity 尝试使用；重试可在 Run 仍有效时重新兑换。所有兑换记录审计事件，但不记录明文。

### 5.3 阶段事件

新增内部阶段事件写入接口，Worker 在以下阶段记录开始/完成/失败：

```text
preparing
credential_lease
authenticating
executing
waiting
collecting
evaluating
cleanup
```

事件载荷只允许白名单字段，不允许 Cookie、Header、请求体、密码和 Token。

## 6. Agent 版本与运行快照

Agent 版本 `target_config` 保持：

```json
{
  "login": {"strategy": "browser_profile"},
  "browser_profile_id": "..."
}
```

发布前校验：

- `strategy=browser_profile` 时必须选择同项目浏览器实例。
- 浏览器实例必须具有 `ready` 登录态；缺失时版本可保存草稿，但不能发布或启动 Run。
- Run 快照保存浏览器实例 ID、快照版本和摘要，不保存明文或信封。
- 已发布 Agent 版本不可因浏览器实例后续更新而被静默改写；Run 创建时固定当次快照版本。

## 7. TapNow 执行流程

1. Workflow 根据 `adapter_id=tapnow-canvas*` 路由到 TapNow Activity。
2. Activity 根据登录策略：
   - `browser_profile`：兑换 Storage State 并跳过账号密码表单登录；
   - `username_password/credential`：兑换项目凭证并执行显式登录；
   - `none`：不注入身份，但仍校验目标未重定向到登录页。
3. 创建每 RunCase 独立的临时 BrowserContext：
   - 注入 Storage State；
   - 开启录像；
   - 开启 Playwright Trace（screenshots、snapshots，不包含源码）；
   - 注册控制台错误和网络摘要采集器。
4. 访问目标 URL，插件判断认证状态。若进入登录页，返回 `AuthExpired`，不自动切换策略。
5. 插件执行只读安全检查、提交测试意图并等待目标状态变化。
6. 完成态必须来自明确的完成标记、目标任务状态或可验证的稳定终态。
7. `Ask before acting`、确认弹窗或高风险操作请求属于 `awaiting_confirmation`：
   - 只读模式不点击，返回 `review_required`；
   - 人工确认模式创建审核任务并等待后续批准，不自动执行。
8. 采集 Canvas JSON、节点、连线、工具调用、最终页面状态和媒体引用。
9. 关闭上下文后上传截图、录像、Trace、网络摘要和控制台错误。
10. 回写统一 Evidence，清除 Storage State、凭证和临时目录。

运行过程中产生的新 Cookie 默认不回写浏览器实例，避免并发污染和隐式身份变更。用户显式重新登录后才生成新快照。

## 8. Artifact 与脱敏

每个关键浏览器 RunCase至少生成：

- `final.png`
- `video.webm`（浏览器产生时）
- `playwright-trace.zip`
- `network-summary.json`
- `console-errors.json`
- `canvas.json`

网络摘要仅记录方法、脱敏 URL、状态码、资源类型、时长和失败类型，不记录请求/响应 Body、Cookie、Authorization 或完整查询密钥。URL 查询参数使用允许列表，其余值替换为 `[REDACTED]`。

Artifact 正文存对象存储，数据库只保存项目隔离的描述符、摘要和关联 ID。失败路径也应尽最大可能上传已产生证据。

## 9. 状态与错误分类

- `ValidationError`：未选择浏览器实例、目标域不匹配、配置非法；不重试。
- `PermissionError`：跨项目实例、租约无权、登录态缺失；不重试。
- `AuthExpired`：加载快照后仍进入登录页；不重试，提示用户重新登录。
- `AwaitingConfirmation`：目标要求人工确认；RunCase 进入审核闭环，不视为成功。
- `TargetProductError`：目标站 5xx、额度不足、任务失败或画布错误；按策略有限重试或记录失败。
- `TransientError`：临时网络错误；有限重试。
- `PlatformError`：CDP 导出、解密、Temporal 契约、Artifact 上传等平台缺陷；告警且不得伪装成目标失败。
- `CancelledError`：用户取消；立即停止页面操作、关闭上下文并上传已有证据。

Run 的技术状态、质量结论和安全结论继续独立保存。

## 10. 前端体验

### 浏览器实例页

- 展示实例运行状态、登录态状态、最后登录和最后验证时间。
- 提供“启动并登录”“保存登录态”“验证登录态”“停止”操作。
- 登录态过期时显示明确修复入口，不展示任何 Cookie 信息。

### Agent 版本页

- 选择“用已登录浏览器”后，只显示同项目浏览器实例。
- 显示 `ready/expired/missing` 状态；非 `ready` 状态阻止发布。

### Run 详情页

- 时间线显示认证、执行、等待、采集和清理阶段。
- 展示截图、录像、Trace、网络摘要、控制台错误和 Canvas 结构入口。
- `AuthExpired`、`AwaitingConfirmation`、目标额度不足和平台错误使用不同文案与处理动作。

## 11. 测试与验收

### 11.1 自动测试

- Domain：浏览器实例状态、快照版本、项目隔离和发布校验。
- 加密：AAD 绑定、篡改拒绝、错误项目/实例拒绝、密钥轮换兼容。
- Repository：真实 PostgreSQL CRUD、唯一约束、索引和项目隔离。
- API：权限、CSRF、内部 Token、跨项目租约、Run/RunCase 归属和响应脱敏。
- Migration：空库到 `0019`、`0018 -> 0019`、旧 JSON 显式幂等导入。
- Worker：Storage State 仅存在于 Activity、Temporal 历史无敏感字段、重试重新租约、取消与清理。
- Playwright：专用 Fake Target 完成“登录 → 导出 → 停止实例 → 新上下文恢复 → 执行 Agent → Artifact 上传”。
- Plugin：登录页识别、明确完成态、待确认态、额度不足、危险动作阻断和 Canvas 提取。
- 前端：状态展示、发布拦截、错误恢复和 Artifact 入口。

### 11.2 故障注入

- 过期 Cookie。
- 被篡改的加密信封。
- Worker 在兑换后和 Artifact 上传前重启。
- 并发 RunCase 使用同一浏览器实例。
- 目标超时、5xx、额度不足和确认弹窗。
- Artifact 上传部分失败。
- 用户取消和 Temporal 重放。

### 11.3 上线验收

必须同时满足：

1. 前端 format、lint、typecheck、测试和 production build 全部通过。
2. 后端 Ruff、mypy、单元、集成、契约、架构和迁移测试全部通过。
3. Worker Workflow replay、重试、取消、幂等、重启和敏感数据扫描通过。
4. Fake Target 全栈成功 Run 产生完整 Artifact、评分、审核和门禁闭环。
5. 使用真实 TapNow 专用账号完成至少一个只读成功 Run，记录 Run ID、RunCase ID、Artifact ID、评分、安全结果和 Gate 决策。
6. 真实目标外部额度或账号状态阻塞时，任务保持“阻塞”，不得标记完成或上线。

## 12. 发布与回滚

- 数据库先执行 Expand：新增表和字段，不删除旧 JSON。
- 部署 Control API 与新 Worker后运行显式导入命令并核对数量。
- 验证新路径后停止旧 JSON 写入；保留只读备份一个发布周期。
- 回滚应用时保留 `0019` 数据，不将明文导出回 JSON。
- 如需数据库 downgrade，先撤销新 Worker、导出加密信封备份并确认没有依赖新快照的运行中 Run。

## 13. 非目标

- 不自动处理 CAPTCHA、MFA、短信验证码或第三方授权确认。
- 不自动刷新登录态或保存运行产生的新 Cookie。
- 不把浏览器实例目录挂载给 Worker。
- 不允许插件直接访问登录态仓库。
- 不在本阶段建设通用远程 Browser Farm；接口为后续 Browser Session Service 保留边界。

## 14. 规格自检

- 无待定字段、占位实现或 Mock 生产路径。
- 登录态事实源、加密边界、Worker 权限和运行快照语义一致。
- 浏览器停止后执行、Worker 重启、并发隔离和错误闭环均有明确行为。
- 真实成功 Run 是上线硬门禁，外部条件不足时不会被自动降级。
