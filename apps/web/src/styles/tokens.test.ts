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

  it("reveals shared tooltips only for visible keyboard focus", () => {
    expect(globalStyles).toContain(
      ".app-tooltip-trigger:has(:focus-visible) > .app-tooltip-content",
    );
    expect(globalStyles).toContain(
      ".app-tooltip-trigger:has(:focus:not(:focus-visible)) > .app-tooltip-content",
    );
  });
});
