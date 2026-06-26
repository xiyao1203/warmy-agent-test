# M4: 画布 Agent 插件与多模态评测 Implementation Plan

> **Goal:** 建立画布 Agent 插件体系，通过 Canvas Adapter 接入画布 Agent API，采集节点/连线/执行状态，输出结构断言和多模态评分。

**Architecture:** 插件只依赖公开 Plugin SDK，不导入控制面内部模块。断言引擎在控制面扩展，支持画布结构和多模态评测。

---

## File Structure

```text
plugins/canvas-agent/
├── src/agenttest_plugin_canvas/
│   ├── __init__.py
│   ├── adapter.py          # CanvasAgentAdapter
│   ├── manifest.json         # Plugin manifest
│   └── schemas/            # Canvas JSON schemas
├── tests/
│   └── test_adapter.py
└── pyproject.toml

apps/control-api/src/agenttest/modules/
└── plugins/                # Plugin registry (new module)
    ├── domain/
    ├── application/
    ├── infrastructure/
    └── public.py
```

### Task 1: Plugin SDK 基座

- [x] 创建 `plugins/canvas-agent/` 目录和 pyproject.toml
- [x] 定义 Canvas 插件 Manifest
- [x] 实现 CanvasAgentAdapter 核心接口

### Task 2: 画布结构断言

- [ ] 节点存在性断言
- [ ] 连线正确性断言
- [ ] 孤立节点检测
- [ ] 画布 JSON Schema 校验

### Task 3: 多模态评分适配

- [ ] DeepEval 适配层
- [ ] 图片 Prompt 一致性评分
- [ ] 参考图相似度评分

### Task 4: 插件注册与控制面集成

- [ ] 控制面插件注册表
- [ ] 插件发现与加载
