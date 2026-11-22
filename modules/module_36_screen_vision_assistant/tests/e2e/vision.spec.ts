import { expect, test } from "@playwright/test";

test("Screen Vision Assistant HUD renders SVG overlay and creates a sample capture", async ({ page }) => {
  await page.goto("http://127.0.0.1:8136/vision");
  await expect(page.getByText("Screen Vision Assistant")).toBeVisible();
  await page.getByRole("button", { name: /Create Sample Screen Capture/i }).click();
  await expect(page.locator("#vision-svg")).toBeVisible();
});
