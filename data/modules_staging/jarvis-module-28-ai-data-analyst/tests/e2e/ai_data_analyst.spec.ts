import { test, expect } from '@playwright/test';

test.describe('Module 28 — AI Data Analyst E2E', () => {
  test('loads control UI and ingests CSV dataset', async ({ page }) => {
    await page.goto('http://127.0.0.1:8128/ai-data-analyst');
    await expect(page.locator('h1')).toContainText('AI Data Analyst');
    await page.fill('#dName', 'E2E Revenue');
    await page.click('button:has-text("+ Ingest & Profile CSV")');
    await expect(page.locator('#activeTitle')).toContainText('E2E Revenue');
  });
});
