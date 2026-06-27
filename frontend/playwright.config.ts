import { defineConfig, devices } from "@playwright/test";

// E2E runs against a running app. Start backend (:8000) and frontend (:5173)
// first, then: `npm run test:e2e`. Override the target with BASE_URL.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    { name: "mobile-chromium", use: { ...devices["Pixel 7"] } },
  ],
});
