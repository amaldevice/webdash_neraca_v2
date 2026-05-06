import { test, expect } from "@playwright/test";
import path from "node:path";
import { LandingPage } from "./pages/LandingPage";
import { UploadPage } from "./pages/UploadPage";

test.describe("smoke", () => {
  test("landing has title and aggregate cards region", async ({ page }) => {
    const landing = new LandingPage(page);
    await landing.goto();
    await expect(page).toHaveTitle(/Sistem Data BPS/);
    await expect(page.getByRole("navigation")).toBeVisible();
  });

  test("navigate to upload via Unggah Data link", async ({ page }) => {
    const landing = new LandingPage(page);
    await landing.goto();
    await landing.unggahDataLink().click();
    await expect(page).toHaveURL(/\/upload$/);
    const upload = new UploadPage(page);
    await expect(upload.excelSectionHeading()).toBeVisible();
    await expect(upload.pengunggahInput()).toBeVisible();
  });

  test("input manual page reachable", async ({ page }) => {
    const landing = new LandingPage(page);
    await landing.goto();
    await landing.inputManualLink().click();
    await expect(page).toHaveURL(/\/manual$/);
    await expect(page.getByRole("heading", { name: "Input Data Manual" })).toBeVisible();
  });

  test("preview page can be opened from landing", async ({ page }) => {
    const landing = new LandingPage(page);
    await landing.goto();
    await expect(page.getByRole("link", { name: "Pratinjau Data" })).toBeVisible();
    await landing.unggahDataLink().click();
    await expect(page).toHaveURL(/\/upload$/);
    await page.getByRole("link", { name: "Lihat Pratinjau" }).click();
    await expect(page).toHaveURL(/\/preview-data$/);
    await expect(page.getByRole("heading", { name: "Filter Pratinjau" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Tabel Pratinjau Data" })).toBeVisible();
  });

  /** GitHub #58 — universal long template (nama_dataset, indikator, periode, nilai) → pratinjau. */
  test("universal template upload reaches preview panel", async ({ page }) => {
    const landing = new LandingPage(page);
    const upload = new UploadPage(page);

    await landing.goto();
    await landing.unggahDataLink().click();
    await expect(page.locator('input[name="csrf_token"]')).toHaveAttribute("value", /.+/);
    await upload.pengunggahInput().fill("E2E Universal Playwright");
    await upload
      .fileInput()
      .setInputFiles(path.join(process.cwd(), "static", "e2e_universal_template.xlsx"));
    await upload.previewButton().click();

    await expect(upload.previewSectionHeading()).toBeVisible();
    await expect(upload.previewDataSampleHeading()).toBeVisible();
  });

  test("upload file picker can trigger preview panel", async ({ page }) => {
    const landing = new LandingPage(page);
    const upload = new UploadPage(page);

    await landing.goto();
    await landing.unggahDataLink().click();
    await upload.pengunggahInput().fill("E2E Tester Playwright");
    await upload.fileInput().setInputFiles(path.join(process.cwd(), "static", "e2e_agent_browser.xlsx"));
    await upload.previewButton().click();

    await expect(upload.previewSectionHeading()).toBeVisible();
    await expect(upload.previewDataSampleHeading()).toBeVisible();
  });

  test("preview link from upload form remains reachable after upload preview", async ({ page }) => {
    const landing = new LandingPage(page);
    const upload = new UploadPage(page);

    await landing.goto();
    await landing.unggahDataLink().click();
    await upload.pengunggahInput().fill("E2E Tester Playwright 2");
    await upload.fileInput().setInputFiles(path.join(process.cwd(), "static", "e2e_agent_browser.xlsx"));
    await upload.previewButton().click();

    await expect(upload.previewSectionHeading()).toBeVisible();
    await page.getByRole("link", { name: "Lihat Pratinjau" }).click();
    await expect(page).toHaveURL(/\/preview-data$/);
    await expect(page.getByRole("heading", { name: "Tabel Pratinjau Data" })).toBeVisible();
  });
});
