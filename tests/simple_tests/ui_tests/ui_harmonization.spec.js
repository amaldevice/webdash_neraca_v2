const path = require('path');
const fs = require('fs');
const { test, expect } = require('../../metadata/node_modules/@playwright/test');

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5000';
const OUTPUT_DIR = path.join(process.cwd(), 'simple_tests', 'test_results', 'ui_harmonization');

const pages = [
  { name: 'landing', path: '/' },
  { name: 'upload', path: '/upload' },
  { name: 'manual', path: '/manual' },
  { name: 'preview', path: '/preview-data' },
  { name: 'management', path: '/data-management' }
];

const ensureOutputDir = () => {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
};

const readStyleSignature = async (page) => {
  return page.evaluate(() => {
    const panel = document.querySelector('.panel');
    const primaryButton = document.querySelector('.btn-primary');
    const topbar = document.querySelector('.app-topbar');

    const pick = (element) => {
      if (!element) return null;
      const style = window.getComputedStyle(element);
      return {
        borderRadius: style.borderRadius,
        minHeight: style.minHeight,
        backgroundColor: style.backgroundColor,
        borderColor: style.borderColor,
      };
    };

    return {
      panel: pick(panel),
      primaryButton: pick(primaryButton),
      topbar: pick(topbar),
    };
  });
};

test.describe('UI harmonization consistency', () => {
  test.beforeAll(async () => {
    ensureOutputDir();
  });

  test('all key pages share the same visual foundations', async ({ page }) => {
    let baseline = null;

    for (const target of pages) {
      await page.setViewportSize({ width: 1440, height: 1100 });
      await page.goto(`${BASE_URL}${target.path}`, { waitUntil: 'networkidle' });

      await expect(page.locator('.app-topbar')).toBeVisible();
      await expect(page.locator('#main-content')).toBeVisible();
      await expect(page.locator('.navbar-end .topbar-nav-link').first()).toBeVisible();
      await expect(page.locator('.panel').first()).toBeVisible();

      const styleSignature = await readStyleSignature(page);
      expect(styleSignature.panel).not.toBeNull();
      expect(styleSignature.topbar).not.toBeNull();

      if (!baseline) {
        baseline = styleSignature;
      } else {
        expect(styleSignature.panel.borderRadius).toBe(baseline.panel.borderRadius);
        expect(styleSignature.topbar.backgroundColor).toBe(baseline.topbar.backgroundColor);
        if (styleSignature.primaryButton && baseline.primaryButton) {
          expect(styleSignature.primaryButton.borderRadius).toBe(baseline.primaryButton.borderRadius);
          expect(styleSignature.primaryButton.minHeight).toBe(baseline.primaryButton.minHeight);
        }
      }

      await page.screenshot({
        path: path.join(OUTPUT_DIR, `${target.name}.png`),
        fullPage: true,
      });
    }
  });

  test('table-driven pages expose the shared table shell', async ({ page }) => {
    for (const target of [
      { name: 'preview', path: '/preview-data' },
      { name: 'management', path: '/data-management' },
    ]) {
      await page.setViewportSize({ width: 1440, height: 1100 });
      await page.goto(`${BASE_URL}${target.path}`, { waitUntil: 'networkidle' });

      await expect(page.locator('.table-wrap')).toHaveCount(1, { timeout: 10000 });
      await expect(page.locator('nav[aria-label*="Paginasi"]').first()).toBeVisible();
    }
  });
});
