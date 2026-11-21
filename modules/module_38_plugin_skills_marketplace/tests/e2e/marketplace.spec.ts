import { expect, test } from "@playwright/test";

test("Plugin & Skills Marketplace HUD publishes a sample skill", async ({ page }) => {
  await page.goto("http://127.0.0.1:8138/marketplace");
  await expect(page.getByText("Plugin & Skills Marketplace")).toBeVisible();
  await page.getByRole("button", { name: /Publish Sample Skill/i }).click();
  await expect(page.getByText("Daily Briefing Skill")).toBeVisible();
});
