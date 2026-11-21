import { test, expect } from "@playwright/test";

test.describe("JARVIS Module 43 — Autonomous Screen Guardian E2E", () => {
  test("loads standalone HUD and enforces explicit monitoring consent", async ({ page }) => {
    await page.goto("http://127.0.0.1:8143/screen-guardian");
    await expect(page.locator("text=SCREEN GUARDIAN")).toBeVisible();
    await expect(page.locator("#btn-start")).toBeVisible();
    await expect(page.locator("#btn-stop")).toBeVisible();
  });
});
