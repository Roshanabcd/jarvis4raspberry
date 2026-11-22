import { expect, test } from "@playwright/test";

test("Backup & Recovery Manager HUD creates a workspace snapshot", async ({ page }) => {
  await page.goto("http://127.0.0.1:8139/backups");
  await expect(page.getByText("Backup & Recovery Manager")).toBeVisible();
  await page.getByRole("button", { name: /Create Workspace Snapshot/i }).click();
  await expect(page.getByText("Workspace Snapshot")).toBeVisible();
});
