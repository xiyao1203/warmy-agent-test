# CI/CD 集成指南

本文档介绍如何将 Agent Test Platform 集成到 CI/CD 流程中。

## 概述

Agent Test Platform 提供标准的测试报告格式，可与主流 CI/CD 工具集成：

- **JUnit XML**: Jenkins、GitLab CI、CircleCI
- **JSON**: 自定义集成
- **HTML**: 人类可读报告

## GitHub Actions 集成

### 基本用法

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Agent Tests
        run: |
          # 调用测试运行 API
          curl -X POST "http://your-server/api/v1/projects/{project_id}/runs" \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            -d '{"plan_id": "your-plan-id"}'
      
      - name: Generate Report
        uses: ./.github/workflows/templates/test-report.yml
        with:
          run_id: ${{ steps.run.outputs.run_id }}
          format: junit
```

### PR 评论

当在 Pull Request 中运行测试时，会自动在 PR 中添加评论，包含测试结果摘要。

## 报告格式

### JUnit XML

标准 JUnit XML 格式，适用于大多数 CI 工具：

```xml
<?xml version="1.0" ?>
<testsuites>
  <testsuite name="run-123" tests="10" failures="2" time="5.000">
    <testcase name="case-1" time="1.000" />
    <testcase name="case-2" time="2.000">
      <failure message="AssertionError">expected 'A' but got 'B'</failure>
    </testcase>
  </testsuite>
</testsuites>
```

### JSON

```json
{
  "format_version": "1.0",
  "generated_at": "2026-06-29T10:00:00Z",
  "run_id": "run-123",
  "total_cases": 10,
  "passed_cases": 8,
  "failed_cases": 2,
  "cases": [...]
}
```

### HTML

生成人类可读的 HTML 报告，包含统计卡片和详细表格。

## API 端点

```
GET /api/v1/projects/{project_id}/runs/{run_id}/reports/{format}
```

**参数：**
- `project_id`: 项目 ID
- `run_id`: 运行 ID
- `format`: 报告格式 (`json` | `junit` | `html`)

**示例：**

```bash
# 生成 JUnit 报告
curl "http://localhost:8000/api/v1/projects/proj-1/runs/run-1/reports/junit" \
  -o report.xml

# 生成 HTML 报告
curl "http://localhost:8000/api/v1/projects/proj-1/runs/run-1/reports/html" \
  -o report.html
```

## 最佳实践

1. **测试失败时生成报告**：即使测试失败，也应生成报告以便分析
2. **保存报告为构建产物**：使用 `actions/upload-artifact` 保存报告
3. **设置失败阈值**：配置 CI 在测试失败率超过阈值时中断
4. **并行运行**：对于大型测试套件，考虑并行运行以加快速度

## 故障排查

### 报告生成失败

1. 检查 API 服务器是否运行
2. 确认 `run_id` 存在
3. 检查格式参数是否正确

### CI 集成问题

1. 确保 API Token 有效
2. 检查网络连接
3. 查看 CI 日志获取详细错误信息
