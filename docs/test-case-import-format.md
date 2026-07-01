# Test Case Import Format

支持三种格式导入测试用例：**JSON**、**JSONL**、**CSV**。

## 文件大小限制

单次导入最大 **10MB**。

## 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 用例名称，不可为空 |
| `input` | object | 输入参数（JSON 对象），不可为空对象 |
| `execution_mode` | enum | 执行模式：`api` / `browser` / `canvas` / `hybrid` |

## 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `assertions` | list[object] | 断言规则列表 |
| `scorers` | list[object] | 评分器配置列表 |
| `initial_state` | object | 初始状态 |
| `expected_outcome` | object | 期望输出 |
| `security_policies` | list[object] | 安全策略列表 |
| `tags` | list[string] | 标签列表 |
| `scenario` | string | 场景描述 |
| `priority` | enum | 优先级：`P0` / `P1` / `P2` / `P3` |
| `risk_level` | enum | 风险等级：`critical` / `high` / `medium` / `low` |
| `difficulty` | string | 难度描述 |
| `test_group` | enum | 分组：`train` / `validation` / `test` |
| `sort_order` | int | 排序序号 |

## JSON 格式

```json
[
  {
    "name": "问候 API 正常响应",
    "input": { "message": "你好" },
    "execution_mode": "api",
    "priority": "P1",
    "tags": ["smoke", "regression"]
  },
  {
    "name": "浏览器登录流程",
    "input": { "url": "https://example.com/login" },
    "execution_mode": "browser",
    "assertions": [{ "type": "contains", "value": "欢迎" }]
  }
]
```

## JSONL 格式

每行一个 JSON 对象，空行自动跳过。

```jsonl
{"name":"问候 API","input":{"message":"你好"},"execution_mode":"api","priority":"P0"}
{"name":"浏览器登录","input":{"url":"https://example.com/login"},"execution_mode":"browser","assertions":[{"type":"contains","value":"欢迎"}]}
```

## CSV 格式

首行为列名，JSON 字段（`input`、`assertions`、`scorers`、`initial_state`、`expected_outcome`、`security_policies`、`tags`）使用 JSON 字符串表示。

```csv
name,input,execution_mode,priority,tags
问候 API,"{""message"":""你好""}",api,P1,"[""smoke""]"
浏览器登录,"{""url"":""https://example.com/login""}",browser,P0,"[""e2e""]"
```

## 错误报告

预览和导入失败时返回结构化错误，每行可包含多个字段错误：

```json
{
  "valid_count": 1,
  "errors": [
    { "line": 2, "field": "execution_mode", "code": "invalid_enum", "message": "execution_mode must be one of: api, browser, canvas, hybrid" },
    { "line": 3, "field": "name", "code": "invalid_value", "message": "name must be non-empty" }
  ],
  "preview": [ ... ]
}
```

错误码：
- `required`：缺少必填字段
- `invalid_type`：字段类型不正确
- `invalid_enum`：枚举值不在允许范围内
- `invalid_value`：字段值无效（如空名称）
- `unknown_field`：不支持的字段

## 导入规则

1. **全量或全无**：任一行出错，整批导入回滚，不产生部分数据。
2. **仅草稿版本**：已发布版本不可导入。
3. **预览优先**：建议先调用预览接口检查数据有效性，确认无误后再执行导入。
# 测试用例导入格式

测试用例只能导入到数据集的**草稿版本**。平台先执行预检；存在任意错误时不会写入任何用例。单次文件上限为 10MB，支持 JSON、JSONL 和 CSV。

## 必填字段

| 字段 | 类型 | 用途 |
|---|---|---|
| `name` | 非空字符串 | 用例名称 |
| `input` | JSON 对象 | 发送给被测 Agent 的输入变量 |
| `execution_mode` | `api`、`browser`、`canvas` 或 `hybrid` | 选择执行引擎；当前通用 HTTP Agent 链执行 `api` 用例 |

## 可选字段

`initial_state`、`expected_outcome` 必须是对象；`assertions`、`scorers`、`security_policies` 必须是对象数组；`tags` 必须是字符串数组。还可填写 `scenario`、`priority`、`risk_level`、`difficulty`、`test_group` 和 `sort_order`。

## JSON 示例

```json
[
  {
    "name": "问候响应",
    "input": {"message": "你好"},
    "execution_mode": "api",
    "expected_outcome": {"contains": "你好"},
    "assertions": [{"type": "contains", "value": "你好"}],
    "tags": ["冒烟", "中文"]
  }
]
```

JSONL 每行放一个与上例数组元素相同的 JSON 对象。CSV 必须使用同名表头；对象或数组字段填写合法 JSON，例如 `{"message":"你好"}`、`[{"type":"contains","value":"你好"}]`。

预检错误包含 `line`、`field`、`code`、`message`，可直接定位到行和字段。预检通过后执行正式导入，再发布数据集版本；发布版本会被测试计划引用并在创建 Run 时固化为不可变快照。
