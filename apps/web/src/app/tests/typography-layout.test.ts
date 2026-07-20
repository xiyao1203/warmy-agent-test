import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("root typography fonts", () => {
  const layout = readFileSync(
    resolve(process.cwd(), "src/app/layout.tsx"),
    "utf8",
  );

  it("self-hosts the UI, Chinese fallback, and technical fonts", () => {
    expect(layout).toContain(
      'import { Geist, Geist_Mono, Noto_Sans_SC } from "next/font/google"',
    );
    expect(layout).toContain('variable: "--font-geist"');
    expect(layout).toContain('variable: "--font-geist-mono"');
    expect(layout).toContain('variable: "--font-noto-sans-sc"');
    expect(layout).toContain("geist.variable");
    expect(layout).toContain("geistMono.variable");
    expect(layout).toContain("notoSansSc.variable");
  });
});
