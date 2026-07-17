import { ArrowDown, ArrowUp, Copy, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";

import { AssertionEditor } from "./test-case-editors";
import { newFormRowId } from "./test-case-form-codecs";
import type { TestStepRow } from "./test-case-professional-fields";

export function TestCaseStepEditor({
  onChange,
  rows,
}: {
  onChange: (rows: TestStepRow[]) => void;
  rows: TestStepRow[];
}) {
  function update(id: string, patch: Partial<TestStepRow>) {
    onChange(rows.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  }

  function move(index: number, offset: -1 | 1) {
    const target = index + offset;
    if (target < 0 || target >= rows.length) return;
    const next = [...rows];
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  }

  return (
    <div>
      <div>
        <h3 className="text-sm font-medium">标准操作步骤</h3>
        <p className="mt-1 text-xs text-[var(--muted)]">
          每步分别填写操作、测试数据、预期结果和机器断言，保存时自动连续编号。
        </p>
      </div>
      <div className="mt-3 space-y-4">
        {rows.map((row, index) => (
          <fieldset
            className="rounded-[var(--radius-md)] border border-[var(--hairline)] p-4"
            key={row.id}
          >
            <legend className="px-1 text-sm font-semibold">
              步骤 {index + 1}
            </legend>
            <div className="space-y-3">
              <label className="block text-xs font-medium">
                操作 <span className="text-[var(--danger)]">*</span>
                <Input
                  aria-label={`步骤 ${index + 1} 操作`}
                  className="mt-1.5"
                  onChange={(event) =>
                    update(row.id, { action: event.target.value })
                  }
                  placeholder="清晰描述执行者要完成的动作"
                  value={row.action}
                />
              </label>
              <div className="rounded-[var(--radius-md)] bg-[var(--surface-subtle)] p-3">
                <div className="text-xs font-medium">
                  浏览器自动化动作（可选）
                </div>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  浏览器用例标记为就绪前，每个步骤都必须配置结构化动作；上方操作仍保留给人工阅读。
                </p>
                <div className="mt-2 grid gap-2 md:grid-cols-3">
                  <DropdownSelect
                    aria-label={`步骤 ${index + 1} 自动化动作`}
                    onChange={(event) =>
                      update(row.id, {
                        operationAction: event.target
                          .value as TestStepRow["operationAction"],
                      })
                    }
                    value={row.operationAction}
                  >
                    <option value="">人工执行 / 暂不配置</option>
                    <option value="goto">打开地址</option>
                    <option value="click">点击</option>
                    <option value="fill">填写</option>
                    <option value="wait">等待元素</option>
                    <option value="screenshot">截图</option>
                  </DropdownSelect>
                  <Input
                    aria-label={`步骤 ${index + 1} 自动化目标`}
                    onChange={(event) =>
                      update(row.id, { operationTarget: event.target.value })
                    }
                    placeholder="URL 或选择器，如 #submit"
                    value={row.operationTarget}
                  />
                  <Input
                    aria-label={`步骤 ${index + 1} 自动化值`}
                    onChange={(event) =>
                      update(row.id, { operationValue: event.target.value })
                    }
                    placeholder="填写动作使用的值"
                    value={row.operationValue}
                  />
                </div>
              </div>
              <label className="block text-xs font-medium">
                测试数据（JSON 对象）
                <textarea
                  aria-label={`步骤 ${index + 1} 测试数据`}
                  className="mt-1.5 min-h-20 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] p-3 font-mono text-xs"
                  onChange={(event) =>
                    update(row.id, { testData: event.target.value })
                  }
                  value={row.testData}
                />
              </label>
              <label className="block text-xs font-medium">
                预期结果 <span className="text-[var(--danger)]">*</span>
                <Input
                  aria-label={`步骤 ${index + 1} 预期结果`}
                  className="mt-1.5"
                  onChange={(event) =>
                    update(row.id, { expectedResult: event.target.value })
                  }
                  placeholder="描述本步骤可观察、可验证的结果"
                  value={row.expectedResult}
                />
              </label>
              <AssertionEditor
                onChange={(assertions) => update(row.id, { assertions })}
                rows={row.assertions}
              />
            </div>
            <div className="mt-3 flex justify-end gap-1 border-t border-[var(--hairline)] pt-3">
              <Button
                aria-label={`上移步骤 ${index + 1}`}
                disabled={index === 0}
                onClick={() => move(index, -1)}
                variant="ghost"
              >
                <ArrowUp aria-hidden="true" className="size-4" />
              </Button>
              <Button
                aria-label={`下移步骤 ${index + 1}`}
                disabled={index === rows.length - 1}
                onClick={() => move(index, 1)}
                variant="ghost"
              >
                <ArrowDown aria-hidden="true" className="size-4" />
              </Button>
              <Button
                aria-label={`复制步骤 ${index + 1}`}
                onClick={() => {
                  const copy = {
                    ...row,
                    assertions: row.assertions.map((item) => ({
                      ...item,
                      id: newFormRowId(),
                    })),
                    artifacts: row.artifacts.map((item) => ({
                      ...item,
                      id: newFormRowId(),
                    })),
                    id: newFormRowId(),
                  };
                  onChange([
                    ...rows.slice(0, index + 1),
                    copy,
                    ...rows.slice(index + 1),
                  ]);
                }}
                variant="ghost"
              >
                <Copy aria-hidden="true" className="size-4" />
              </Button>
              <Button
                aria-label={`删除步骤 ${index + 1}`}
                onClick={() =>
                  onChange(rows.filter((item) => item.id !== row.id))
                }
                variant="ghost"
              >
                <Trash2 aria-hidden="true" className="size-4" />
              </Button>
            </div>
          </fieldset>
        ))}
      </div>
      <Button
        className="mt-3"
        onClick={() =>
          onChange([
            ...rows,
            {
              action: "",
              artifacts: [],
              assertions: [],
              expectedResult: "",
              id: newFormRowId(),
              operationAction: "",
              operationTarget: "",
              operationValue: "",
              testData: "{}",
            },
          ])
        }
        variant="secondary"
      >
        <Plus aria-hidden="true" className="mr-1 size-4" />
        添加操作步骤
      </Button>
    </div>
  );
}
