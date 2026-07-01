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
