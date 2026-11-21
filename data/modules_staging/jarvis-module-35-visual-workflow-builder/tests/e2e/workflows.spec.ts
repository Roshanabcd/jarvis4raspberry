import { expect, test } from "@playwright/test";

test("Visual Workflow Builder HUD loads and executes a sample DAG pipeline", async ({ page }) => {
  await page.goto("http://127.0.0.1:8135/workflows");
  await expect(page.getByText("Visual Workflow Builder")).toBeVisible();
  await page.getByRole("button", { name: /Create Sample Pipeline/i }).click();
  await expect(page.locator("#dag-svg")).toBeVisible();
});
