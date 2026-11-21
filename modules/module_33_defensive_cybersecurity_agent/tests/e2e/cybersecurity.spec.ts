import { test, expect } from "@playwright/test";

test("Module 33 Defensive Cybersecurity HUD loads and displays posture", async ({ page }) => {
  await page.goto("http://127.0.0.1:8133/cybersecurity");
  await expect(page.getByText("JARVIS // DEFENSIVE CYBERSECURITY AGENT")).toBeVisible();
  await expect(page.getByText("Security Posture")).toBeVisible();
});
