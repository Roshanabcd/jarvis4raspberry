import { expect, test } from "@playwright/test";

test("Permissions & Approval Center HUD submits and approves a high-risk request", async ({ page }) => {
  await page.goto("http://127.0.0.1:8140/approvals");
  await expect(page.getByText("Permissions & Approval Center")).toBeVisible();
  await page.getByRole("button", { name: /Submit Sample High-Risk Request/i }).click();
  await expect(page.getByText(/Deploy JARVIS release/i)).toBeVisible();
});
