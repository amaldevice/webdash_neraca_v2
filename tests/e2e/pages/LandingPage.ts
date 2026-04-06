import { type Locator, type Page } from "@playwright/test";

export class LandingPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto(): Promise<void> {
    await this.page.goto("/");
  }

  /** Scoped to desktop main nav (landing may duplicate CTAs with the same text). */
  unggahDataLink(): Locator {
    return this.page.getByLabel("Navigasi utama desktop").getByRole("link", { name: "Unggah Data" });
  }

  inputManualLink(): Locator {
    return this.page.getByLabel("Navigasi utama desktop").getByRole("link", { name: "Input Manual" });
  }
}
