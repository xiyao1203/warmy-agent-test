import type {
  HTMLAttributes,
  TableHTMLAttributes,
  TdHTMLAttributes,
  ThHTMLAttributes,
} from "react";

export function Table({
  className = "",
  ...props
}: TableHTMLAttributes<HTMLTableElement>) {
  return (
    <div className="min-w-0 overflow-x-auto">
      <table
        className={`w-full table-auto border-collapse text-center text-[13px] ${className}`}
        {...props}
      />
    </div>
  );
}

export function TableHeader(props: HTMLAttributes<HTMLTableSectionElement>) {
  return <thead {...props} />;
}

export function TableBody(props: HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody {...props} />;
}

export function TableRow({
  className = "",
  ...props
}: HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={`border-b border-[var(--hairline)] transition-colors last:border-b-0 hover:bg-[var(--canvas-soft)] ${className}`}
      {...props}
    />
  );
}

export function TableHead({
  className = "",
  ...props
}: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={`h-9 bg-[var(--surface-inset)] px-3 text-center text-xs font-medium text-[var(--muted)] ${className}`}
      {...props}
    />
  );
}

export function TableCell({
  className = "",
  ...props
}: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={`h-11 min-w-0 px-3 text-center align-middle ${className}`}
      {...props}
    />
  );
}

export function TableValue({
  className = "",
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`mx-auto w-fit max-w-full text-left ${className}`}
      {...props}
    />
  );
}
