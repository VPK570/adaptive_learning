import { test, expect } from '@playwright/test';

test.describe('Auth Guards', () => {
  for (const path of ['/student/dashboard', '/faculty/dashboard', '/admin/dashboard']) {
    test(`unauthenticated user redirected from ${path}`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL('/', { timeout: 10000 });
    });
  }

  test('student layout renders nothing for non-student role', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => {
      window.localStorage.setItem('uniauth', JSON.stringify({
        state: {
          token: 'fake',
          user: { email: 'admin@test.edu', role: 'admin', name: 'Admin' },
          isAuthenticated: true,
        },
        version: 0,
      }));
    });
    await page.goto('/student/dashboard');
    await expect(page.locator('body')).not.toContainText('Welcome back');
  });
});
