# Warmy Agent Test

面向开发与测试团队的通用 Agent 自动化测试、安全评估与发布门禁平台。

首个落地场景是 AI 创作画布 Agent，后续通过插件扩展客服、RAG、浏览器、工作流、Coding 和语音 Agent。

## 当前状态

项目处于 M0 开发准备阶段，产品需求、技术架构和 AI 开发协作规范已经完成，应用代码尚未初始化。

当前工作见：

- [当前任务](./docs/当前任务.md)
- [开发进度与变更记录](./docs/开发进度与变更记录.md)

## 核心文档

- [产品需求文档](./docs/Agent测试平台产品需求文档-PRD.md)
- [技术架构与开发规范](./docs/Agent测试平台技术架构与开发规范.md)
- [Codex 开发指南](./docs/Codex开发指南.md)
- [AI 开发协作规范](./AGENTS.md)

## 使用 Codex 开发

从仓库根目录启动 Codex，让它先确认已读取项目指令：

```bash
codex --ask-for-approval never "请列出你加载的项目指令，并用不超过 8 行总结当前任务、允许修改范围、架构约束和验收方式。不要修改文件。"
```

开始开发时可以使用：

```text
请按 AGENTS.md 开始当前任务。
先读取 docs/当前任务.md、开发进度和相关需求/架构，
复述范围与验收方式后再执行。
完成后运行验证，更新当前任务和开发进度记录。
```

更完整的开发、续接、评审和交接提示词见 [Codex 开发指南](./docs/Codex开发指南.md)。

## 架构摘要

```text
Next.js Web 控制台
        ↓
FastAPI 模块化单体控制面
        ↓
Temporal 工作流
        ↓
API / Playwright / Browser Harness / Evaluation / Security Workers
```

业务数据使用 PostgreSQL，对象产物使用 MinIO/S3，Redis 仅用于缓存和短期协调。

## GitHub

仓库：<https://github.com/xiyao1203/warmy-agent-test>

