import { defineConfig, devices } from "@playwright/test";

/**
 * E2E smoke against local Flask. Starts app without debug reloader (single process).
 * Run: npm ci && npx playwright install chromium && npm run test:e2e
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:5000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command:
      "python -c \"from app import app; app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)\"",
    url: "http://127.0.0.1:5000/",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
