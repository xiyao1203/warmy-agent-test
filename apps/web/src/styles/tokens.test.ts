import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("GLM workspace design tokens", () => {
  const tokens = readFileSync(
    resolve(process.cwd(), "src/styles/tokens.css"),
    "utf8",
  );
  const globalStyles = readFileSync(
    resolve(process.cwd(), "src/app/globals.css"),
    "utf8",
  );

  it("defines coral product accents and precision workspace density tokens", () => {
    expect(tokens).toContain("--primary: #e94b43");
    expect(tokens).toContain("--control-height-sm: 32px");
    expect(tokens).toContain("--sidebar-width: 208px");
    expect(tokens).toContain("--sidebar-width-collapsed: 56px");
    expect(tokens).toContain("--navigation-row-height: 34px");
    expect(tokens).toContain("--icon-optical-size: 17px");
    expect(tokens).toContain("--metric-height: 88px");
    expect(tokens).toContain("--shadow-overlay:");
  });

  it("defines semantic motion durations for floating and spatial UI", () => {
    expect(tokens).toContain("--motion-micro: 120ms");
    expect(tokens).toContain("--motion-fast: 160ms");
    expect(tokens).toContain("--motion-dialog: 220ms");
    expect(tokens).toContain("--motion-drawer: 260ms");
    expect(tokens).toContain("--motion-spatial: 280ms");
  });

  it("defines theme-aware chromatic navigation tones and motion fallbacks", () => {
    for (const tone of ["coral", "blue", "mint", "amber", "indigo"]) {
      expect(
        tokens.match(new RegExp(`--navigation-${tone}:`, "g")),
      ).toHaveLength(2);
      expect(globalStyles).toContain(
        `.app-nav-link[data-navigation-tone="${tone}"]`,
      );
    }

    expect(globalStyles).toContain("background: var(--navigation-tone)");
    expect(globalStyles).toMatch(
      /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.app-nav-icon[\s\S]*?transform: none/,
    );
  });

  it("defines a complete explicit dark theme", () => {
    expect(tokens).toMatch(/\.dark\s*\{/);
    expect(tokens).toContain("--canvas: #111113");
    expect(tokens).toContain("--primary: #ff6b61");
  });

  it("does not duplicate the dialog centering translation in keyframes", () => {
    const dialogKeyframes = globalStyles.match(
      /@keyframes precision-dialog-in\s*\{[\s\S]*?\n\}/,
    );

    expect(dialogKeyframes?.[0]).toBeDefined();
    expect(dialogKeyframes?.[0]).not.toContain("translate(-50%");
  });

  it("does not position shared tooltips inside their trigger overflow context", () => {
    expect(globalStyles).not.toContain(
      ".app-tooltip-trigger:has(:focus-visible) > .app-tooltip-content",
    );
    expect(globalStyles).not.toContain(
      ".app-tooltip-trigger:has(:focus:not(:focus-visible)) > .app-tooltip-content",
    );
  });

  it("keeps global and command search visually borderless", () => {
    expect(globalStyles).toMatch(
      /\.app-search-trigger\s*\{[\s\S]*?border:\s*0;[\s\S]*?background:\s*transparent;/,
    );
    expect(globalStyles).toMatch(
      /\.app-command-search-input,\s*\.app-command-search-input:focus,\s*\.app-command-search-input:focus-visible\s*\{[\s\S]*?border:\s*0;[\s\S]*?box-shadow:\s*none;[\s\S]*?outline:\s*none;/,
    );
    expect(globalStyles).toContain(".app-command-search:focus-within");
  });

  it("defines the approved developer-platform typography system", () => {
    const normalizedTypographyTokens = tokens
      .replace(/\s+/g, " ")
      .toLowerCase();

    expect(normalizedTypographyTokens).toContain(
      '--font-sans: var(--font-geist), "source han sans sc"',
    );
    expect(normalizedTypographyTokens).toContain(
      '--font-code: var(--font-geist-mono), "source code pro"',
    );
    expect(tokens).toContain("--text-page-title-size: 26px");
    expect(tokens).toContain("--text-page-title-line-height: 36px");
    expect(tokens).toContain("--text-page-title-weight: 600");
    expect(tokens).toContain("--text-page-title-letter-spacing: -0.02em");
    expect(tokens).toContain("--text-section-title-size: 18px");
    expect(tokens).toContain("--text-section-title-line-height: 28px");
    expect(tokens).toContain("--text-card-title-size: 16px");
    expect(tokens).toContain("--text-card-title-line-height: 24px");
    expect(tokens).toContain("--text-body-size: 14px");
    expect(tokens).toContain("--text-body-line-height: 22px");
    expect(tokens).toContain("--text-secondary-size: 13px");
    expect(tokens).toContain("--text-secondary-line-height: 20px");
    expect(tokens).toContain("--text-caption-size: 12px");
    expect(tokens).toContain("--text-caption-line-height: 18px");
    expect(tokens).toContain("--text-code-size: 13px");
    expect(tokens).toContain("--text-code-line-height: 22px");
    expect(normalizedTypographyTokens).toContain("--ink: #101828");
    expect(normalizedTypographyTokens).toContain("--body: #344054");
    expect(normalizedTypographyTokens).toContain("--muted: #475467");
    expect(normalizedTypographyTokens).toContain("--muted-soft: #667085");
    expect(normalizedTypographyTokens).toContain("--ink: #f5f7fa");
    expect(normalizedTypographyTokens).toContain("--body: #d0d5dd");
    expect(normalizedTypographyTokens).toContain("--muted: #98a2b3");
    expect(globalStyles).toContain("font-variant-numeric: tabular-nums");
    expect(globalStyles).toContain("font-variant-ligatures: none");
  });

  it("exposes semantic typography utilities and compatible base scales", () => {
    for (const semanticClass of [
      "text-page-title",
      "text-section-title",
      "text-card-title",
      "text-body",
      "text-secondary",
      "text-caption",
      "text-code",
      "text-button",
      "text-badge",
      "text-table-head",
      "text-table-cell",
    ]) {
      expect(globalStyles).toContain(`.${semanticClass}`);
    }

    expect(globalStyles).toMatch(
      /\.text-xs\s*\{[\s\S]*?font-size: var\(--text-caption-size\)/,
    );
    expect(globalStyles).toMatch(
      /\.text-sm\s*\{[\s\S]*?font-size: var\(--text-body-size\)/,
    );
    expect(globalStyles).toMatch(
      /\.text-base\s*\{[\s\S]*?font-size: var\(--text-card-title-size\)/,
    );
    expect(globalStyles).toMatch(
      /\.text-lg\s*\{[\s\S]*?font-size: var\(--text-section-title-size\)/,
    );
    expect(globalStyles).toMatch(
      /\.text-2xl\s*\{[\s\S]*?font-size: var\(--text-page-title-size\)/,
    );
    expect(globalStyles).toMatch(
      /\.font-mono\s*\{[\s\S]*?font-family: var\(--font-code\)/,
    );
  });

  it("applies the approved sidebar typography without changing its geometry", () => {
    expect(globalStyles).toMatch(
      /\.app-nav-label\s*\{[\s\S]*?font-size: var\(--text-caption-size\);[\s\S]*?font-weight: 500;[\s\S]*?letter-spacing: 0\.02em;/,
    );
    expect(globalStyles).toMatch(
      /\.app-nav-link\s*\{[\s\S]*?font-size: var\(--text-body-size\);[\s\S]*?font-weight: 400;/,
    );
    expect(globalStyles).toMatch(
      /\.app-nav-link\[data-active="true"\]\s*\{[\s\S]*?font-weight: 600;/,
    );
    expect(globalStyles).toContain("height: var(--navigation-row-height)");
  });
});
