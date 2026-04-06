import { type Locator, type Page } from "@playwright/test";

export class UploadPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto(): Promise<void> {
    await this.page.goto("/upload");
  }

  excelSectionHeading(): Locator {
    return this.page.getByRole("heading", { name: "Unggah Berkas Excel" });
  }

  pengunggahInput(): Locator {
    return this.page.getByRole("textbox", { name: "Pengunggah" });
  }

  previewButton(): Locator {
    return this.page.getByRole("button", { name: "Unggah & Pratinjau" });
  }
}
