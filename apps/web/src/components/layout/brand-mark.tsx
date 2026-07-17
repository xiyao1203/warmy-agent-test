"use client";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={`brand-mark ${compact ? "brand-mark-compact" : ""}`}
      data-brand-mark="agent-test-glyph"
      data-brand-mark-source="warmy-product-system"
    >
      <svg
        className="brand-mark-glyph"
        fill="none"
        viewBox="0 0 32 32"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect
          className="brand-mark-surface"
          height="28"
          rx="8"
          width="28"
          x="2"
          y="2"
        />
        <path
          className="brand-mark-spark"
          d="M16 7.5c.5 4.75 3.75 8 8.5 8.5-4.75.5-8 3.75-8.5 8.5-.5-4.75-3.75-8-8.5-8.5 4.75-.5 8-3.75 8.5-8.5Z"
        />
        <circle className="brand-mark-core" cx="16" cy="16" r="2.5" />
      </svg>
    </span>
  );
}
