import { test, expect } from '@playwright/test';

test.describe('Faculty Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/faculty/dashboard');
  });

  test('dashboard renders with stats', async ({ page }) => {
    await expect(page.getByText('Faculty Dashboard')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Total Students')).toBeVisible();
    await expect(page.getByText('Active Courses')).toBeVisible();
    await expect(page.getByText('Avg Engagement')).toBeVisible();
  });

  test('add course button opens modal', async ({ page }) => {
    await page.getByText('Add Course').click();
    await expect(page.getByText('Add New Course')).toBeVisible();
  });

  test('sidebar nav has faculty items', async ({ page }) => {
    await expect(page.getByText('Analytics')).toBeVisible();
  });
});

test.describe('Generate Question Paper', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/faculty/generate');
  });

  test('config form renders', async ({ page }) => {
    await expect(page.getByText('Question Paper Generator')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Paper Configuration')).toBeVisible();
    await expect(page.getByText("Bloom's Taxonomy Levels")).toBeVisible();
    await expect(page.getByText('Sections')).toBeVisible();
  });

  test('bloom level checkboxes toggle', async ({ page }) => {
    const remember = page.getByText('Remember').first();
    await remember.click();
  });

  test('paper summary panel renders', async ({ page }) => {
    await expect(page.getByText('Paper Summary')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Course')).toBeVisible();
    await expect(page.getByText('Duration')).toBeVisible();
    await expect(page.getByText('Total Marks')).toBeVisible();
  });
});
