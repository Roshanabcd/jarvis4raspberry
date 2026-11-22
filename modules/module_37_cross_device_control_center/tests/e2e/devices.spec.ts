import { expect, test } from "@playwright/test";

test("Cross-Device Control Center HUD registers a sample mesh node", async ({ page }) => {
  await page.goto("http://127.0.0.1:8137/devices");
  await expect(page.getByText("Cross-Device Control Center")).toBeVisible();
  await page.getByRole("button", { name: /Register Sample Pi 5 Node/i }).click();
  await expect(page.getByText("Roshan-Pi5-Node")).toBeVisible();
});
