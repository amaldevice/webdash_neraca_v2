# Matriks kontrak dataset (Fase 0)

Sumber struktur detail: `docs/superpowers/plans/2026-04-16-dataset-aware-upload-manual-refactor.md` dan `services/dataset_catalog.py`.

| Slug (internal) | Label UI | `source_sheet` (nama lembar Excel BI) | `time_period_mode` | `table_type` |
| --- | --- | --- | --- | --- |
| `pinjaman` | Pinjaman | `pinjaman` | monthly | three_way |
| `simpanan` | Simpanan | `simpanan` | monthly | three_way |
| `ecommerce` | E-commerce | `ecommerce` | quarterly | two_way |
| `atm` | ATM / Debet | `ATM` | monthly | two_way |
| `kartu_kredit` | Kartu kredit | `Kartu kredit ` (spasi trailing) | monthly | two_way |
| `uang_elektronik` | Uang elektronik | `UANG ELEKTRONIK` | monthly | two_way |
| `indikator_sekda_bi` | Indikator sekda BI | `Indikator sekda BI` | monthly | three_way |

## Dikecualikan dari katalog / UI

- `Resume`, `PMSE`, `Perkembangan Indikator` — tidak ada entri di `dataset_catalog`.

## Legacy upload

- Tanpa `dataset_slug`: parser tetap boleh (lembar pertama / auto) selama `REQUIRE_DATASET_FOR_UPLOAD` tidak di-set truthy.
- Mode ketat: set env `REQUIRE_DATASET_FOR_UPLOAD=1` — form wajib memilih dataset; `parse_excel_payload(..., require_dataset_context=True)` menolak parse bila slug kosong.

## Verifikasi cepat

- `python -m pytest tests/test_excel_parser.py tests/test_upload_flow.py tests/test_upload_template_route.py tests/test_app_factory.py -q`
