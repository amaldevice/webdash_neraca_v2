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

  test('Aggregated plot and period analysis request period filters', async ({ page }) => {
    const apiPayloads = {
      plot: [],
      pivot: [],
    };

    page.on('request', request => {
      if (request.url().endsWith('/generate-plot') && request.method() === 'POST') {
        apiPayloads.plot.push(request.postData() || '');
      }
      if (request.url().endsWith('/generate-period-analysis') && request.method() === 'POST') {
        apiPayloads.pivot.push(request.postData() || '');
      }
    });

    await page.goto(`${BASE_URL}/aggregated`, { waitUntil: 'domcontentloaded' });

    const indicatorFilter = page.locator('#indicator_filter');
    await expect(indicatorFilter).toBeVisible();
    const indicatorOptions = await indicatorFilter.locator('option').count();

    // Skip if no indicators available yet.
    test.skip(indicatorOptions <= 1, 'No indicators available for aggregated analysis.');

    const indicatorValue = await indicatorFilter.locator('option').nth(1).getAttribute('value');
    if (indicatorValue === null) {
      throw new Error('Unable to pick aggregated indicator option.');
    }
    await indicatorFilter.selectOption(indicatorValue);

    await page.locator('#start_period').fill('2024');
    await page.locator('#end_period').fill('2024-Q4');
    await page.locator('#time_range').selectOption('all');
    await page.locator('#generate-plot').click();

    await page.locator('#plot-display svg').first().waitFor({ state: 'visible', timeout: 12000 });
    expect(apiPayloads.plot.length).toBeGreaterThan(0);

    const sentPlot = apiPayloads.plot[apiPayloads.plot.length - 1];
    expect(sentPlot).toContain('period_start=2024');
    expect(sentPlot).toContain('end_period=2024-Q4');

    const analysisIndicator = page.locator('#analysis_indicator');
    await expect(analysisIndicator).toBeVisible();
    await analysisIndicator.selectOption(indicatorValue);
    await page.locator('#analysis_year').selectOption({ index: 0 });
    await page.locator('#period_start').fill('2023');
    await page.locator('#period_end').fill('2024');
    await page.locator('#generate-pivot').click();

    await page.locator('#pivot-result').waitFor({ state: 'visible', timeout: 12000 });
    expect(apiPayloads.pivot.length).toBeGreaterThan(0);

    const sentPivot = apiPayloads.pivot[apiPayloads.pivot.length - 1];
    expect(sentPivot).toContain('period_start=2023');
    expect(sentPivot).toContain('end_period=2024');
  });
});
