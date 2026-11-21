import { test, expect } from '@playwright/test';

test.describe('Module 29 — Advanced File Manager E2E', () => {
  test('loads control UI and creates a file', async ({ page }) => {
    await page.goto('http://127.0.0.1:8129/file-manager');
    await expect(page.locator('h1')).toContainText('Advanced File Manager');
    await page.fill('#fPath', 'e2e_note.md');
    await page.fill('#fContent', '# Hello from E2E');
    await page.click('button:has-text("Save File")');
    await expect(page.locator('#fileList')).toContainText('e2e_note.md');
  });
});
