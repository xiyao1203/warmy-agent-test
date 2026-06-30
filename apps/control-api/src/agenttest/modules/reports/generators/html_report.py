"""HTML 报告生成器。"""

from __future__ import annotations

import html
from datetime import UTC, datetime
from typing import Any


class HtmlReportGenerator:
    """HTML 格式报告生成器。

    生成人类可读的 HTML 报告。
    """

    def generate(self, run_data: dict[str, Any]) -> str:
        """生成 HTML 报告。

        Args:
            run_data: 运行数据。

        Returns:
            HTML 字符串。
        """
        run_id = run_data.get("run_id", "")
        total = int(run_data.get("total_cases", 0))  # type: ignore[arg-type]
        passed = int(run_data.get("passed_cases", 0))  # type: ignore[arg-type]
        failed = int(run_data.get("failed_cases", 0))  # type: ignore[arg-type]
        cases = run_data.get("cases", [])  # type: ignore[assignment]

        # 生成用例表格行
        case_rows = ""
        for case in cases:
            status_class = "passed" if case.get("status") == "passed" else "failed"
            status_text = "通过" if case.get("status") == "passed" else "失败"
            case_rows += f"""
            <tr class="{status_class}">
              <td>{html.escape(str(case.get("case_id", "")))}</td>
              <td>{status_text}</td>
              <td>{case.get("duration_ms", 0)}ms</td>
              <td>{html.escape(str(case.get("error", "-")))}</td>
            </tr>
            """

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>测试报告 - {html.escape(str(run_id))}</title>
  <style>
    body {{
      font-family: -apple-system, sans-serif;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }}
    .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
    .card {{ padding: 20px; border-radius: 8px; text-align: center; }}
    .card.total {{ background: #e3f2fd; }}
    .card.passed {{ background: #e8f5e9; }}
    .card.failed {{ background: #ffebee; }}
    .card h2 {{ margin: 0; font-size: 2em; }}
    .card p {{ margin: 5px 0 0; color: #666; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
    tr.failed {{ background: #fff5f5; }}
    tr.passed {{ background: #f5fff5; }}
  </style>
</head>
<body>
  <h1>测试报告</h1>
  <p>运行 ID: {html.escape(str(run_id))}</p>
  
  <div class="summary">
    <div class="card total">
      <h2>{total}</h2>
      <p>总用例</p>
    </div>
    <div class="card passed">
      <h2>{passed}</h2>
      <p>通过</p>
    </div>
    <div class="card failed">
      <h2>{failed}</h2>
      <p>失败</p>
    </div>
    <div class="card">
      <h2>{passed / total * 100 if total > 0 else 0:.1f}%</h2>
      <p>通过率</p>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>用例 ID</th>
        <th>状态</th>
        <th>耗时</th>
        <th>错误</th>
      </tr>
    </thead>
    <tbody>
      {case_rows}
    </tbody>
  </table>
  
  <p style="margin-top: 40px; color: #999;">
    生成时间: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")} UTC
  </p>
</body>
</html>"""
