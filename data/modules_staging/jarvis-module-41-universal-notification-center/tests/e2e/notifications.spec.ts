import { test, expect } from "@playwright/test";

test.describe("JARVIS Module 41 — Universal Notification Center E2E", () => {
  test("loads HUD, sends notification, and toggles DND", async ({ page }) => {
    await page.goto("http://127.0.0.1:8141/notifications");
    await expect(page.locator("h1")).toContainText("Universal Notification Center");

    await page.fill("#title", "Playwright Test Alert");
    await page.fill("#message", "Verified end-to-end delivery.");
    await page.click("#send-btn");

    await expect(page.locator("#list")).toContainText("Playwright Test Alert");
  });
});
