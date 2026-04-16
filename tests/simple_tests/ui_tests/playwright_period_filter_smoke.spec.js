const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://127.0.0.1:5000';

const submitFilterForm = async (page) => {
  const form = page.locator('form').filter({ has: page.locator('#start_period') });
  await expect(form).toHaveCount(1);

  const submitBtn = form.locator('button:has-text("Terapkan Filter")');
  await expect(submitBtn).toBeVisible();

  await Promise.all([
    page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
    submitBtn.click(),
  ]);
};

test.describe('Period range filter smoke checks', () => {
  test('Preview-Data keeps start_period and end_period in filter flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/preview-data`, { waitUntil: 'domcontentloaded' });

    const startInput = page.locator('#start_period');
    const endInput = page.locator('#end_period');
    await expect(startInput).toBeVisible();
    await expect(endInput).toBeVisible();

    await startInput.fill('2024');
    await endInput.fill('2024-Q2');

    await submitFilterForm(page);

    await expect(page).toHaveURL(/start_period=2024/);
    await expect(page).toHaveURL(/end_period=2024-Q2/);

    await expect(startInput).toHaveValue('2024');
    await expect(endInput).toHaveValue('2024-Q2');
  });

  test('Data-Management sends period filters via GET form', async ({ page }) => {
    await page.goto(`${BASE_URL}/data-management`, { waitUntil: 'domcontentloaded' });

    const startInput = page.locator('#start_period');
    const endInput = page.locator('#end_period');
    await expect(startInput).toBeVisible();
    await expect(endInput).toBeVisible();

    await startInput.fill('2024');
    await endInput.fill('2025');

    await submitFilterForm(page);

    await expect(page).toHaveURL(/data-management/);
    await expect(page).toHaveURL(/start_period=2024/);
    await expect(page).toHaveURL(/end_period=2025/);

    await expect(startInput).toHaveValue('2024');
    await expect(endInput).toHaveValue('2025');
  });

});
