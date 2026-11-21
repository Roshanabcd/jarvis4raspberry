import { test, expect } from "@playwright/test";

test("Module 30 Smart Home Controller HUD loads and displays telemetry", async ({ page }) => {
  await page.goto("http://127.0.0.1:8130/smart-home");
  await expect(page.getByText("JARVIS // SMART HOME CONTROLLER")).toBeVisible();
  await expect(page.getByText("System Telemetry")).toBeVisible();
});
