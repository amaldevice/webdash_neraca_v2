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

  versionInput(): Locator {
    return this.page.getByRole("textbox", { name: "Versi" });
  }

  fileInput(): Locator {
    return this.page.locator("#excel_file");
  }

  previewButton(): Locator {
    return this.page.getByRole("button", { name: "Unggah & Pratinjau" });
  }

  previewSectionHeading(): Locator {
    return this.page.getByRole("heading", { name: "Ringkasan Pratinjau Unggahan" });
  }

  previewDataSampleHeading(): Locator {
    return this.page.locator("details summary", { hasText: "Contoh data yang akan disimpan" });
  }
}
