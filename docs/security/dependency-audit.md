# 依赖供应链审计

## 2026-07-16 审计结论

- Node 和 Python 生产依赖均为零已知漏洞；门禁已从高危收紧为中危起阻断。
- Control API 将 `pydantic-ai` 元包替换为精确固定的 `pydantic-ai-slim==1.102.0`，关闭 0.7.2 中允许不可信消息历史触发任意 URL 请求的 SSRF，以及后续 IPv6 转换地址绕过修复，同时避免元包的 Temporal extra 将仓库的 `temporalio==1.29.0` 降级到 1.20.0。
- `browser-harness` 升级到 0.1.5；其元数据仍错误固定已知有漏洞的 `Pillow==12.2.0`，仓库通过 uv 根级精确 Override 使用兼容的 `Pillow==12.3.0`。截图打开、绘制与保存冒烟以及完整 Python 回归通过。
- Next.js 16.2.9 固定的 PostCSS 8.4.31 存在 `GHSA-qx2v-qp2m-jg93` 中危 XSS；pnpm Workspace 对 `next>postcss` 精确覆盖为仓库已使用的 8.5.15，生产构建和完整 Web 回归通过。

## 自动化门禁

运行：

```bash
make security-audit
```

该命令执行 `pnpm audit --prod --audit-level moderate`，并从 `uv.lock` 导出带 Hash 的全部生产 Python 精确版本。`pip-audit --no-deps --disable-pip` 直接审计这份完整锁定集合，避免安全 Override 被 pip 按上游错误元数据二次解析；临时需求文件退出时自动删除，不写入凭证。当前没有漏洞忽略项。

## 验证记录

- 初始 `pnpm audit --prod --audit-level high`：发现 PostCSS 中危 1 项，无高危或严重项。
- 初始 `pip-audit`：发现 Pydantic AI SSRF 2 项、Pillow 上游固定版本漏洞 5 项；升级到 1.56.0 后审计又识别出两个后续 SSRF 绕过公告，因此最终固定到同时修复它们的 1.102.0。
- 2026-07-16 复核发现 Pillow 12.2.0 新增 3 项公告且均由 12.3.0 修复；升级 Browser Harness、覆盖 Pillow 并移除 5 项旧忽略后，Python 审计为 `No known vulnerabilities found`。
- 覆盖 Next.js 的 PostCSS 后，`pnpm audit --prod --audit-level moderate` 为 `No known vulnerabilities found`。
- `uv run pytest apps/control-api/tests/unit/test_agent apps/control-api/tests/contract/test_super_agent_chat_api.py -q`：46 项通过。
- 最终审计、类型检查和完整回归结果记录在 `docs/开发进度与变更记录.md`。

## 复核与回滚

- 复核时间：每次锁文件、Next.js 或 `browser-harness` 版本变化时；上游解除错误固定后删除对应 Override，并重新生成 Lockfile。
- 回滚：只能回到仍包含 Pillow 12.3.0 和 PostCSS 8.5.15 修复的依赖组合；不得回退到已确认有漏洞的传递版本。
- 许可证：`pydantic-ai-slim`、Browser Harness、Pillow 和 PostCSS 未引入新的生产依赖许可证类别。
