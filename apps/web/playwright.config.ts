import { defineConfig } from "@playwright/test";

const webPort = Number(process.env.E2E_WEB_PORT ?? 5175);

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30000,
  retries: 0,
  use: {
    baseURL: `http://localhost:${webPort}`,
    headless: true,
    viewport: { width: 1280, height: 720 },
  },
  webServer: {
    command: "cd ../.. && bash scripts/start_e2e_server.sh",
    port: webPort,
    reuseExistingServer: false,
    timeout: 120000,
  },
});
