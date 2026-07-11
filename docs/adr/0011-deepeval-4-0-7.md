# ADR-0011：DeepEval 固定为 4.0.7

- 状态：已接受
- 日期：2026-07-11

## 背景

技术架构原记录 DeepEval 4.0.5。实施 TapNow 生产测试闭环时，PyPI 当前稳定版为 4.0.7（2026-06-22 发布），许可证为 Apache-2.0，支持 Python 3.12，并保留 `LLMTestCase`、`ToolCall` 和 Metric `measure` 接口。

## 决策

API Runner 精确固定 `deepeval==4.0.7`。DeepEval 仅在 Worker Activity/Adapter 内运行，返回平台 `CaseScore`；不成为数据集、Run 或报告事实来源。

## 后果

- Lockfile 固定全部传递依赖。
- 升级必须重新校验指标语义、分数漂移、模型调用和结果 Schema。
- SDK 或模型配置缺失时明确返回环境错误，不降级为启发式通过。
