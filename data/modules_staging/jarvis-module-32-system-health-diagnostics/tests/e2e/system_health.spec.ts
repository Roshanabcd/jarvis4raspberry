import { test, expect } from "@playwright/test";

test("Module 32 System Health HUD loads and displays live telemetry", async ({ page }) => {
  await page.goto("http://127.0.0.1:8132/system-health");
  await expect(page.getByText("JARVIS // SYSTEM HEALTH & DIAGNOSTICS")).toBeVisible();
  await expect(page.getByText("Live Host Telemetry")).toBeVisible();
});
