import { test, expect } from "@playwright/test";
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
});
