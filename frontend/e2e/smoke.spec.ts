import { expect, test } from "@playwright/test";

// Smoke tests that only need the frontend running. Extend with full flows
// (register → admin approve → tournament → score → bracket → finalize) once
// you point BASE_URL at an environment with the backend up.

test("landing renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Table Tennis Tournaments/i })).toBeVisible();
});

test("login form is reachable and accessible", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: /Sign in/i })).toBeVisible();
  // aria-label falls back to placeholder, so fields are reachable by name.
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: /Sign in/i })).toBeVisible();
});

test("register form is reachable", async ({ page }) => {
  await page.goto("/register");
  await expect(page.getByLabel("Display name")).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
});
