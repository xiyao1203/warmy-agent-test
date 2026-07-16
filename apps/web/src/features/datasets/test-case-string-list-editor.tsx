import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { newFormRowId } from "./test-case-form-codecs";
import type { StringRow } from "./test-case-professional-fields";

export function StringListEditor({
  addLabel,
  label,
  onChange,
  rows,
}: {
  addLabel: string;
  label: string;
  onChange: (rows: StringRow[]) => void;
  rows: StringRow[];
}) {
  return (
    <div>
      <p className="text-sm font-medium">{label}</p>
      <div className="mt-2 space-y-2">
        {rows.map((row, index) => (
          <div className="flex gap-2" key={row.id}>
            <Input
              aria-label={`${label} ${index + 1}`}
              onChange={(event) =>
                onChange(
                  rows.map((item) =>
                    item.id === row.id
                      ? { ...item, value: event.target.value }
                      : item,
                  ),
                )
              }
              placeholder={`${label} ${index + 1}`}
              value={row.value}
            />
            <Button
              aria-label={`删除${label} ${index + 1}`}
              onClick={() =>
                onChange(rows.filter((item) => item.id !== row.id))
              }
              variant="ghost"
            >
              <Trash2 aria-hidden="true" className="size-4" />
            </Button>
          </div>
        ))}
      </div>
      <Button
        className="mt-2"
        onClick={() => onChange([...rows, { id: newFormRowId(), value: "" }])}
        variant="secondary"
      >
        <Plus aria-hidden="true" className="mr-1 size-4" />
        {addLabel}
      </Button>
    </div>
  );
}
