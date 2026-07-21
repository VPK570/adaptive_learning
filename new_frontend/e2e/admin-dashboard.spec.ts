import { test, expect } from '@playwright/test';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/dashboard');
  });

  test('page renders with title', async ({ page }) => {
    await expect(page.getByText('Admin Dashboard')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/platform health/i)).toBeVisible();
  });

  test('overview tab shows stat tiles', async ({ page }) => {
    await expect(page.getByText('Total Users')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Total Courses')).toBeVisible();
    await expect(page.getByText('Docs Processed')).toBeVisible();
    await expect(page.getByText('AI Conversations')).toBeVisible();
  });

  test('overview tab shows users table', async ({ page }) => {
    await expect(page.getByText('All Users').first()).toBeVisible({ timeout: 10000 });
  });

  test('users tab switches from overview', async ({ page }) => {
    await page.getByText('Users').click();
    await expect(page.getByText('All Users')).toBeVisible({ timeout: 10000 });
  });
});
