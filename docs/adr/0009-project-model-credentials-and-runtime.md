# ADR-0009: 项目模型凭证与调用由独立运行边界承载

- Status: Accepted
- Date: 2026-06-29

## Context

测试 Agent 与模型裁判需要项目成员自助配置供应商 API Key，并发起真实模型调用。凭证必须项目隔离、不可回显，长时间评测不能占用控制面进程。

## Decision

模型配置作为控制面独立业务模块持久化；API Key 使用部署主密钥加密。Control API 只发送最小加密配置快照，Model Runner Worker 在 Activity 生命周期内解密并调用 OpenAI-Compatible 服务。每个用途通过项目默认模型显式解析，缺少配置时失败，不使用 Mock 或环境变量供应商 Key 回退。

## Consequences

- 部署必须配置 `AGENTTEST_MODEL_CREDENTIAL_KEY` 并保护、轮换该密钥。
- Worker 不连接业务数据库，只接收当前调用所需快照。
- 模型调用具有独立超时、重试、错误分类和扩缩容边界。
- 后续原生供应商协议通过 Worker Adapter 扩展，不改变项目配置和默认用途模型。

## Alternatives Considered

- 复用环境模板或评分器 JSON：凭证权限、默认用途和调用生命周期边界不清晰。
- Control API 直接调用模型：违反控制面不执行长时间模型评测和 Worker 短生命周期解密约束。
- 全局供应商目录加项目绑定：首期只有一种协议，复杂度超过当前需求。

## Verification

- 项目隔离、权限和凭证不回显集成测试。
- Worker Fake Target、超时、重试和错误分类测试。
- 架构测试禁止控制面导入供应商 SDK或读取供应商 API Key 环境变量。
