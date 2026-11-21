import { test, expect } from "@playwright/test";

test("Module 34 Personal Finance HUD loads and displays summary", async ({ page }) => {
  await page.goto("http://127.0.0.1:8134/finance");
  await expect(page.getByText("JARVIS // PERSONAL FINANCE MANAGER")).toBeVisible();
  await expect(page.getByText("Monthly Cashflow & Net Worth")).toBeVisible();
});
