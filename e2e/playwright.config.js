import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30000,
  retries: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["json", { outputFile: "test-results/results.json" }],
  ],
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile",
      use: { ...devices["iPhone 12"] },
    },
  ],
  // Запускать backend + frontend перед тестами (опционально)
  // webServer: [
  //   { command: "cd ../backend && uvicorn app.main:app --port 8000", port: 8000, reuseExistingServer: true },
  //   { command: "cd ../frontend && npm run dev", port: 5173, reuseExistingServer: true },
  // ],
});
