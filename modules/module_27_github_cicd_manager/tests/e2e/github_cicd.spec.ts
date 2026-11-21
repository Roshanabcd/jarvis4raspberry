import { test, expect } from '@playwright/test';

test.describe('Module 27 — GitHub & CI/CD Manager E2E', () => {
  test('loads control UI and registers a repository', async ({ page }) => {
    await page.goto('http://127.0.0.1:8127/github-cicd');
    await expect(page.locator('h1')).toContainText('GitHub & CI/CD Manager');
    await page.fill('#rName', 'roshan/jarvis-os');
    await page.click('button:has-text("+ Register Repo")');
    await expect(page.locator('#activeRepoTitle')).toContainText('roshan/jarvis-os');
  });
});
