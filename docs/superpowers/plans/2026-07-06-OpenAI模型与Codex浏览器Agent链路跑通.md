# OpenAI 模型与 Codex 浏览器 Agent 链路跑通

## 目标

使用已接入的 OpenAI 模型配置，验证平台从测试 Agent 到 Codex 浏览器执行的真实链路可用；如果链路中断，定位并修复断点。

## 路径

1. 确认本地服务、Temporal、Model Runner、API Runner、Codex CLI 和浏览器依赖状态。
2. 验证项目级 OpenAI-Compatible 模型配置可被 Control API 读取并通过 Model Runner 调用。
3. 验证测试 Agent 对话可以使用项目默认模型生成真实响应。
4. 验证 Codex 浏览器插件可启动浏览器、调用 Codex CLI，并返回真实执行结果。
5. 如需端到端运行，使用已有项目资产或最小化创建测试 Agent / 用例 / 测试计划 / 运行记录，确认执行结果写回平台。

## 验收

- 模型连接测试或测试 Agent 对话返回真实模型响应。
- Codex 浏览器插件真实执行通过，或给出明确外部配置缺失原因。
- API Runner 的 Codex 浏览器 Activity/Workflow 相关测试通过。
- 相关前后端/插件测试通过。

## 风险

- OpenAI API Key、Codex CLI 登录态或网络可能是外部阻塞；如果是配置问题，只记录真实错误，不伪造通过。
- 端到端执行依赖 Temporal、数据库和 Worker 同时在线；若本地服务未启动，先启动并记录。
