import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30000,
  retries: 0,
  use: {
    baseURL: "http://localhost:5175",
    headless: true,
    viewport: { width: 1280, height: 720 },
  },
  webServer: {
    command: "cd ../.. && bash scripts/start_e2e_server.sh",
    port: 5175,
    reuseExistingServer: false,
    timeout: 120000,
  },
});
