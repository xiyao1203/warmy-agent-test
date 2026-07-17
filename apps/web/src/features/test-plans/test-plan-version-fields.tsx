import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";

import type { VersionAssetOption } from "./test-plan-version-dialog";

export function AssetSelectField({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: VersionAssetOption[];
  value: string;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <DropdownSelect
        aria-label={label}
        className="mt-1.5 h-9 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] px-3"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        <option value="">未选择</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </DropdownSelect>
    </label>
  );
}

export function SelectField({
  label,
  onChange,
  options,
  placeholder = "未选择",
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: VersionAssetOption[];
  placeholder?: string;
  value: string;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <DropdownSelect
        aria-label={label}
        className="mt-1.5 h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </DropdownSelect>
    </label>
  );
}

export function parseNumberFieldValue(value: string): number {
  return Number(value);
}

export function NumberField({
  label,
  max,
  min,
  onChange,
  step,
  value,
}: {
  label: string;
  max?: number;
  min: number;
  onChange: (value: number) => void;
  step?: number;
  value: number;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <Input
        className="mt-1.5"
        max={max}
        min={min}
        onChange={(event) =>
          onChange(parseNumberFieldValue(event.target.value))
        }
        step={step}
        type="number"
        value={value}
      />
    </label>
  );
}
