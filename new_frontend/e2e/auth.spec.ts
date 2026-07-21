import { test, expect } from '@playwright/test';

const BACKEND = 'http://localhost:8001';

test.describe('Authentication', () => {

  test('login page renders with all elements', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Vbook LM')).toBeVisible();
    await expect(page.getByText('University AI Platform')).toBeVisible();
    await expect(page.getByText('Sign In')).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
  });

  test('role tabs switch correctly', async ({ page }) => {
    await page.goto('/');
    const tabs = ['Student', 'Faculty', 'Admin'];
    for (const tab of tabs) {
      await page.getByRole('button', { name: tab, exact: true }).click();
      await expect(page.getByRole('button', { name: tab, exact: true })).toHaveClass(/is-active/);
    }
  });

  test('empty email shows validation error', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByText('Email address is required.')).toBeVisible();
  });

  test('invalid email format shows validation error', async ({ page }) => {
    await page.goto('/');
    await page.locator('#email').fill('notanemail');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByText('Please enter a valid email address.')).toBeVisible();
  });

  test('empty password shows validation error', async ({ page }) => {
    await page.goto('/');
    await page.locator('#email').fill('test@test.edu');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByText('Password is required.')).toBeVisible();
  });

  test('wrong credentials show server error', async ({ page }) => {
    await page.goto('/');
    await page.locator('#email').fill('nonexistent@test.edu');
    await page.locator('#password').fill('wrongpass');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByText(/Incorrect|failed|error|Invalid/i)).toBeVisible({ timeout: 10000 });
  });

  test('successful student login and logout', async ({ page }) => {
    const email = `e2e-student-${Date.now()}@test.edu`;
    const password = 'testpass123';

    const res = await page.request.post(`${BACKEND}/auth/register`, {
      data: { email, password, role: 'student' },
    });
    expect(res.ok()).toBeTruthy();

    await page.goto('/');
    await page.locator('#email').fill(email);
    await page.locator('#password').fill(password);
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page).toHaveURL(/\/student\/dashboard/, { timeout: 10000 });
    await expect(page.getByText(/welcome back/i)).toBeVisible();

    await page.evaluate(() => (window as any).useAuthStore?.getState().logout());
    await page.goto('/');
    await page.waitForURL('/');
  });
});
