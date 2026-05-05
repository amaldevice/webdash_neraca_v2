# static/templates/

- **`rekap_dataset_long_templates.xlsx`** — workbook multi-tab (README + satu tab per dataset) berisi **header long-format** dan **dua baris contoh** per dataset, angka diselaraskan dengan `REKAP Bank indonesia_rev.xlsx` di root repo.
- **Pembaruan**: jalankan dari root repo:

  `python scripts/build_rekap_long_templates.py`

  Workbook dibangun dari `services/template_service.build_multi_dataset_reference_workbook` (katalog `services/dataset_catalog.py`).

- Tautan form lama ke `upload_template.xlsx` (horizontal/vertikal generik) tetap path terpisah; template REKAP long-format **belum** otomatis terpasang di UI sampai refactor dataset-aware selesai.
