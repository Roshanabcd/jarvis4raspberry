import { test, expect } from '@playwright/test';

test('Module 22 standalone UI renders and displays simulation badge', async ({ page }) => {
  await page.goto('http://127.0.0.1:8122/model-router');
  await expect(page.getByText('INTELLIGENT AI MODEL ROUTER')).toBeVisible();
  await expect(page.getByText('SIMULATED ADAPTER')).toBeVisible();
});
