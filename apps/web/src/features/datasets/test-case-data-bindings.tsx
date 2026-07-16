import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";

import { newFormRowId } from "./test-case-form-codecs";
import type { DataBindingRow } from "./test-case-professional-fields";

export function TestCaseDataBindings({
  onChange,
  rows,
}: {
  onChange: (rows: DataBindingRow[]) => void;
  rows: DataBindingRow[];
}) {
  function update(id: string, patch: Partial<DataBindingRow>) {
    onChange(rows.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  }

  return (
    <div>
      <div>
        <h3 className="text-sm font-medium">数据绑定</h3>
        <p className="mt-1 text-xs text-[var(--muted)]">
          引用环境、凭证或夹具；敏感数据只保存引用，不保存明文。
        </p>
      </div>
      <div className="mt-3 space-y-3">
        {rows.map((row, index) => {
          const referenceOnly = row.sensitive || row.source !== "literal";
          return (
            <fieldset
              className="rounded-[var(--radius-md)] border border-[var(--hairline)] p-3"
              data-testid={`data-binding-${index + 1}`}
              key={row.id}
            >
              <legend className="px-1 text-xs font-medium">
                绑定 {index + 1}
              </legend>
              <div className="grid gap-3 sm:grid-cols-2">
                <Input
                  aria-label="绑定名称"
                  onChange={(event) =>
                    update(row.id, { name: event.target.value })
                  }
                  placeholder="如 customer_token"
                  value={row.name}
                />
                <DropdownSelect
                  aria-label="数据来源"
                  onChange={(event) => {
                    const source = event.target
                      .value as DataBindingRow["source"];
                    update(row.id, {
                      sensitive: source === "credential" ? true : row.sensitive,
                      source,
                    });
                  }}
                  value={row.source}
                >
                  <option value="literal">固定值</option>
                  <option value="environment">环境变量</option>
                  <option value="credential">凭证引用</option>
                  <option value="fixture">数据夹具</option>
                  <option value="generated">运行时生成</option>
                </DropdownSelect>
                <DropdownSelect
                  aria-label="值类型"
                  onChange={(event) =>
                    update(row.id, {
                      valueType: event.target
                        .value as DataBindingRow["valueType"],
                    })
                  }
                  value={row.valueType}
                >
                  <option value="string">文本</option>
                  <option value="number">数字</option>
                  <option value="boolean">布尔</option>
                  <option value="json">JSON</option>
                </DropdownSelect>
                <Input
                  aria-label="引用"
                  onChange={(event) =>
                    update(row.id, { reference: event.target.value })
                  }
                  placeholder="环境键、凭证 ID 或夹具引用"
                  value={row.reference}
                />
                {!referenceOnly && (
                  <Input
                    aria-label="固定值"
                    onChange={(event) =>
                      update(row.id, { value: event.target.value })
                    }
                    placeholder="非敏感固定值"
                    value={row.value}
                  />
                )}
                <Input
                  aria-label="绑定说明"
                  onChange={(event) =>
                    update(row.id, { description: event.target.value })
                  }
                  placeholder="用途说明"
                  value={row.description}
                />
              </div>
              <div className="mt-3 flex items-center justify-between">
                <label className="flex items-center gap-2 text-xs">
                  <input
                    checked={row.sensitive || row.source === "credential"}
                    disabled={row.source === "credential"}
                    onChange={(event) =>
                      update(row.id, { sensitive: event.target.checked })
                    }
                    type="checkbox"
                  />
                  敏感数据（禁止保存明文）
                </label>
                <Button
                  aria-label={`删除数据绑定 ${index + 1}`}
                  onClick={() =>
                    onChange(rows.filter((item) => item.id !== row.id))
                  }
                  variant="ghost"
                >
                  <Trash2 aria-hidden="true" className="size-4" />
                </Button>
              </div>
            </fieldset>
          );
        })}
      </div>
      <Button
        className="mt-3"
        onClick={() =>
          onChange([
            ...rows,
            {
              description: "",
              id: newFormRowId(),
              name: "",
              reference: "",
              sensitive: false,
              source: "literal",
              value: "",
              valueType: "string",
            },
          ])
        }
        variant="secondary"
      >
        <Plus aria-hidden="true" className="mr-1 size-4" />
        添加数据绑定
      </Button>
    </div>
  );
}
