# 依赖供应链审计

## 2026-07-16 审计结论

- 生产依赖没有未缓解的高危或严重漏洞。
- Control API 将 `pydantic-ai` 元包替换为精确固定的 `pydantic-ai-slim==1.102.0`，关闭 0.7.2 中允许不可信消息历史触发任意 URL 请求的 SSRF，以及后续 IPv6 转换地址绕过修复，同时避免元包的 Temporal extra 将仓库的 `temporalio==1.29.0` 降级到 1.20.0。
- `browser-harness==0.1.3` 仍精确固定 `Pillow==12.2.0`，上游尚未发布兼容 `Pillow==12.3.0` 的版本。当前包仅在可选截图缩放和调试点击覆盖中打开 CDP 自产 PNG；仓库代码不直接导入 Pillow，也不触达受影响的 PCF/BDF 字体、FontFile、GD 或 Windows Viewer 路径。
- Next.js 的生产依赖树仍报告一个 PostCSS 中危漏洞。当前 Next.js 稳定版仍固定受影响版本；本项目不接收、解析并重新序列化用户 CSS，因此不满足公告描述的利用前提。审计仍显示该条目，但高危门禁不会因已记录的中危上游问题阻塞。

## 自动化门禁

运行：

```bash
make security-audit
```

该命令执行 `pnpm audit --prod --audit-level high`，并从锁文件导出全部生产 Python 依赖交给 `pip-audit`。临时需求文件退出时自动删除，不写入凭证。

Pillow 的五个已知公告只在以下失效即失败的约束通过后按公告编号忽略：

1. `browser-harness` 必须仍为 0.1.3；
2. 仓库应用、Worker 和插件不得直接导入 Pillow；
3. 上游包的 Pillow 使用必须仍只位于 `helpers.py`，保持两个导入和两个 `Image.open(path)` 调用；
4. 上游源码不得出现 PCF/BDF/FontFile、GD、ImageShow、WindowsViewer 或 `.show()` 路径。

任一约束变化都会在漏洞忽略生效前令审计失败，防止上游代码变化悄然扩大可达面。忽略列表仅包含 `PYSEC-2026-2253` 至 `PYSEC-2026-2257`，不会压制其他 Pillow 或 Python 依赖漏洞。

## 验证记录

- 初始 `pnpm audit --prod --audit-level high`：发现 PostCSS 中危 1 项，无高危或严重项。
- 初始 `pip-audit`：发现 Pydantic AI SSRF 2 项、Pillow 上游固定版本漏洞 5 项；升级到 1.56.0 后审计又识别出两个后续 SSRF 绕过公告，因此最终固定到同时修复它们的 1.102.0。
- `uv run pytest apps/control-api/tests/unit/test_agent apps/control-api/tests/contract/test_super_agent_chat_api.py -q`：46 项通过。
- 最终审计、类型检查和完整回归结果记录在 `docs/开发进度与变更记录.md`。

## 复核与回滚

- 复核时间：每次锁文件或 `browser-harness` 版本变化时；若无依赖变化，最迟 2026-07-23 再查上游兼容版本。
- 优先动作：上游解除精确固定后升级 Pillow 至 12.3.0 或更高稳定兼容版，并删除对应忽略与可达性门禁。
- 回滚：依赖变更可通过回退本任务提交恢复，但会重新暴露已确认的 Pydantic AI SSRF，不应作为生产环境处置方案。
- 许可证：`pydantic-ai-slim` 与原 Pydantic AI 项目许可证一致；本次未引入新的生产依赖许可证类别。
