"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { Check, ChevronDown } from "lucide-react";
import type {
  ChangeEvent,
  ReactElement,
  ReactNode,
  SelectHTMLAttributes,
} from "react";
import { Children, isValidElement } from "react";

type OptionInfo = {
  disabled: boolean;
  label: ReactNode;
  value: string;
};

type DropdownSelectProps = Omit<
  SelectHTMLAttributes<HTMLSelectElement>,
  "children" | "onChange" | "size"
> & {
  children: ReactNode;
  onChange: (event: ChangeEvent<HTMLSelectElement>) => void;
};

export function DropdownSelect({
  "aria-label": ariaLabel,
  children,
  className = "",
  disabled,
  onChange,
  value,
  ...props
}: DropdownSelectProps) {
  const selectedValue = String(value ?? "");
  const options = extractOptions(children);
  const selected = options.find((option) => option.value === selectedValue);

  function emitChange(nextValue: string) {
    onChange({
      currentTarget: { name: props.name, value: nextValue },
      target: { name: props.name, value: nextValue },
    } as ChangeEvent<HTMLSelectElement>);
  }

  return (
    <>
      <select
        aria-label={ariaLabel}
        className="sr-only"
        disabled={disabled}
        onChange={onChange}
        tabIndex={-1}
        value={selectedValue}
        {...props}
      >
        {children}
      </select>

      <DropdownMenuPrimitive.Root>
        <DropdownMenuPrimitive.Trigger asChild disabled={disabled}>
          <button
            aria-haspopup="listbox"
            className={`app-select-trigger inline-flex h-9 w-full min-w-0 items-center justify-between gap-2 rounded-[var(--radius-md)] border border-[var(--hairline)] px-3 text-left text-sm shadow-none outline-none transition-colors hover:border-[var(--hairline-strong)] hover:bg-[var(--canvas-soft)] focus:border-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
            disabled={disabled}
            type="button"
          >
            <span className="min-w-0 truncate">
              {selected?.label ?? options[0]?.label ?? "请选择"}
            </span>
            <ChevronDown
              aria-hidden="true"
              className="size-4 shrink-0 text-[var(--muted)]"
            />
          </button>
        </DropdownMenuPrimitive.Trigger>
        <DropdownMenuPrimitive.Portal>
          <DropdownMenuPrimitive.Content
            align="start"
            avoidCollisions
            className="precision-menu-content z-50 max-h-72 min-w-[var(--radix-dropdown-menu-trigger-width)] overflow-y-auto rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface-raised)] p-1 shadow-[var(--shadow-overlay)]"
            collisionPadding={8}
            side="bottom"
            sideOffset={6}
          >
            {options.map((option) => (
              <DropdownMenuPrimitive.Item
                className="flex min-h-8 cursor-default select-none items-center gap-2 rounded-[var(--radius-sm)] px-2 text-sm text-[var(--ink)] outline-none data-[disabled]:opacity-50 data-[highlighted]:bg-[var(--canvas-soft)]"
                disabled={option.disabled}
                key={`${option.value}-${String(option.label)}`}
                onSelect={() => emitChange(option.value)}
              >
                <span className="grid size-4 shrink-0 place-items-center">
                  {option.value === selectedValue ? (
                    <Check aria-hidden="true" className="size-4" />
                  ) : null}
                </span>
                <span className="min-w-0 truncate">{option.label}</span>
              </DropdownMenuPrimitive.Item>
            ))}
          </DropdownMenuPrimitive.Content>
        </DropdownMenuPrimitive.Portal>
      </DropdownMenuPrimitive.Root>
    </>
  );
}

function extractOptions(children: ReactNode): OptionInfo[] {
  const options: OptionInfo[] = [];
  Children.forEach(children, (child) => {
    if (!isValidElement(child)) return;
    const option = child as ReactElement<{
      children?: ReactNode;
      disabled?: boolean;
      value?: string | number;
    }>;
    if (option.type !== "option") return;
    const rawValue = option.props.value;
    options.push({
      disabled: Boolean(option.props.disabled),
      label: option.props.children ?? String(rawValue ?? ""),
      value: String(rawValue ?? ""),
    });
  });
  return options;
}
