import { test, expect } from "@playwright/test";

test("Module 31 JARVIS Robot Brain HUD loads and displays telemetry", async ({ page }) => {
  await page.goto("http://127.0.0.1:8131/robot-brain");
  await expect(page.getByText("JARVIS // ROBOT BRAIN")).toBeVisible();
  await expect(page.getByText("Live Robot Telemetry")).toBeVisible();
});
