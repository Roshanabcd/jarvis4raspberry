import { test, expect } from '@playwright/test';

test('Module 24 standalone UI renders header and simulation badge', async ({ page }) => {
  await page.goto('http://127.0.0.1:8124/email-calendar');
  await expect(page.getByText('EMAIL & CALENDAR ASSISTANT')).toBeVisible();
  await expect(page.getByText('SIMULATED MAIL/CAL ADAPTER')).toBeVisible();
});
