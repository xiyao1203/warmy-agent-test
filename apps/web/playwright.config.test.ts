import { describe, expect, it } from "vitest";

import config from "./playwright.config";
import nextConfig from "./next.config";

describe("Playwright web server", () => {
  it("starts an isolated production server from the locked workspace", () => {
    expect(config.webServer).toMatchObject({
      command: "cd ../.. && bash scripts/start_e2e_server.sh",
      reuseExistingServer: false,
      timeout: 120000,
    });
  });

  it("does not hide server races by globally serializing browser tests", () => {
    expect(config.workers).toBeUndefined();
  });

  it("keeps the workspace build directory as the non-E2E default", () => {
    expect(nextConfig.distDir).toBe(".next");
  });
});
