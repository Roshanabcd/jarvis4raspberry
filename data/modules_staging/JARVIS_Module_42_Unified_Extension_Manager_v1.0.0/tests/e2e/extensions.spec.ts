import { test, expect } from "@playwright/test";

test.describe("JARVIS Module 42 — Unified Extension Manager E2E", () => {
  test("loads HUD and renders archive scanner controls", async ({ page }) => {
    await page.goto("http://127.0.0.1:8142/extensions");
    await expect(page.locator("h1")).toContainText("UNIFIED EXTENSION MANAGER");
    await expect(page.locator("#scan-folder")).toBeVisible();
    await expect(page.locator("#scan-btn")).toBeVisible();
  });
});
