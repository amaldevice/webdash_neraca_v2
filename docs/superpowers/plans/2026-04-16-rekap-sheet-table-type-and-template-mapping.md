---
date: 2026-04-16
topic: rekap-sheet-table-type-template-mapping
related: docs/superpowers/plans/2026-04-16-dataset-aware-upload-manual-refactor.md
status: exploration-complete
---

# REKAP `Bank indonesia_rev.xlsx` — Tipe Tabel per Sheet & Pemetaan Template

## Tujuan

- Klasifikasi **One-way / Two-way / Three-way** untuk setiap sheet yang masuk refactor upload/input (bukan definisi matematika abstrak, tapi **jumlah dimensi kategori** yang perlu diidentifikasi sebelum nilai + periode).
- Landasan **satu template long-format per dataset** (selaras refactor utama).
- Sheet **dikecualikan** dari pipeline: `Resume`, `PMSE`, `Perkembangan Indikator` (tidak dianalisis di sini sebagai target ingest).

## Sumber verifikasi

- File master: `REKAP Bank indonesia_rev.xlsx` (root repo, ~670 KiB).
- Inspeksi: `pandas.read_excel(..., header=None, nrows=12–14)` per sheet, `engine=openpyxl`, tanggal **2026-04-16**.

## Definisi operasional (untuk produk upload)

| Tipe | Arti (produk) | Contoh pola |
|------|---------------|--------------|
| **One-way** | Satu dimensi baris/kolom + nilai; tanpa silang kategori kompleks | Deret tunggal indikator × waktu (tidak ada sheet target ingest murni seperti ini di set yang diproses) |
| **Two-way** | **Dua** dimensi non-waktu + nilai, atau satu dimensi baris + **satu** blok waktu di header | Metode pembayaran × (tahun×triwulan); atau baris (jenis transaksi × jenis angka) × bulan |
| **Three-way** | **Tiga+** level/dimensi kategori (sering hierarki indent) **plus** periode | Kelompok bank × rantai sektor × bulan; jenis simpanan × rentang nominal × bulan; indikator × sub-indikator × satuan × bulan |

> Catatan: sheet BI sering **wide** (bulan/triwulan sebagai kolom). Refactor memaksa **long** di template unduhan; tipe tabel di sini menjelaskan **dimensi semantik**, bukan bentuk file.

## Daftar sheet workbook

Urutan tab aktual: `Resume`, `pinjaman`, `simpanan`, `ecommerce`, `ATM`, `Kartu kredit `, `UANG ELEKTRONIK`, `Indikator sekda BI`, `PMSE`, `Perkembangan Indikator`.

**Peringatan nama:** sheet `Kartu kredit ` memiliki **spasi trailing** — katalog `source_sheet` harus cocok persis agar `read_excel` tidak salah sheet.

## Matriks hasil eksplorasi (sheet diproses)

| Sheet (nama persis) | Bentuk wide (ringkas) | Tipe (produk) | Alasan singkat |
|---------------------|------------------------|---------------|----------------|
| `pinjaman` | Baris hierarki: kelompok bank → kelompok pinjaman → sektor; kolom tahun + sub-kolom bulan | **Three-way** | Lokasi nilai = f(kelompok bank / jalur sektor, periode). Selaras bagian “Temuan Eksplorasi Sheet” di refactor plan. |
| `simpanan` | Jenis simpanan (Rupiah/…) → sub-jenis (Giro, …) → rentang nominal; kolom tahun + bulan | **Three-way** | Lokasi nilai = f(jenis simpanan, rentang nominal / sub-level, periode). |
| `ecommerce` | Baris = metode pembayaran; kolom = tahun × Tw I–IV | **Two-way** | Metode × periode (triwulanan). |
| `ATM` | Kolom A = jenis transaksi, B = `Volume`/`Nominal`, header baris tahun + bulan Inggris | **Two-way** | Dimensi baris majemuk (jenis × volume/nominal) × waktu bulanan — tetap **dua** poros kategori + waktu, bukan hierarki sektor tiga level seperti pinjaman. |
| `Kartu kredit ` | Sama seperti `ATM` | **Two-way** | Idem. |
| `UANG ELEKTRONIK` | Sama seperti `ATM` | **Two-way** | Idem; banyak sel kosong di awal periode (data parsial) — ingest harus policy `allow_blank_value` / skip + warning sesuai plan refactor. |
| `Indikator sekda BI` | Kolom: No., Indikator, Satuan, lalu grid bulan per tahun | **Three-way** | Nilai = f(indikator, sub-baris `- …`, satuan, periode). |

### Sheet dikecualikan (bukan target template ingest)

| Sheet | Keterangan singkat |
|-------|-------------------|
| `Resume` | Ringkasan komposit; bukan sumber long-format utama. |
| `PMSE` | Panel khusus; dikecualikan. |
| `Perkembangan Indikator` | Non-data / kosong per plan; dikecualikan. |

## One-way di scope ini

**Tidak ada** sheet target ingest yang cukup dengan satu dimensi kategori saja; semua sheet proses adalah **wide cross-tab** minimal dua poros (+ waktu).

## Kontrak template long-format (ringkas)

Artefak Excel gabungan (satu file, multi-tab slug): `static/templates/rekap_dataset_long_templates.xlsx` — regenerasi: `python scripts/build_rekap_long_templates.py`.

| Slug / tab | Header wajib (urutan disarankan) |
|------------|-----------------------------------|
| `pinjaman` | `kelompok_bank`, `kelompok_pinjaman`, `lapangan_usaha`, `tahun`, `bulan`, `metric_name`, `nilai` |
| `simpanan` | `kelompok_jenis_simpanan`, `produk_simpanan`, `rentang_nominal`, `tahun`, `bulan`, `metric_name`, `nilai` |
| `ecommerce` | `metode_pembayaran`, `tahun`, `triwulan`, `metric_name`, `nilai` |
| `atm`, `kartu_kredit`, `uang_elektronik` | `jenis_transaksi`, `jenis_nilai`, `tahun`, `bulan`, `metric_name`, `nilai` |
| `indikator_sekda_bi` | `no_urut`, `indikator`, `subindikator`, `satuan`, `tahun`, `bulan`, `metric_name`, `nilai` |

Tabel contoh + angka sampel dari sel master: `docs/superpowers/plans/2026-04-16-dataset-aware-upload-manual-refactor.md` § Contoh template per sheet.

`source_sheet` Excel BI untuk kartu kredit: `Kartu kredit ` (spasi akhir). Slug internal tab template: `kartu_kredit`.

## Gap codebase vs workbook (ringkas)

Temuan agen `repo-research-analyst` / `explore`:

- Parser saat ini: `excel_parser/payload.py` membaca **sheet pertama saja**, tanpa `dataset_slug` / `sheet_name`.
- DB: `data_entries` tanpa `dataset_code`; unik `(uploader, version, indicator, year, month, quarter)`.
- Template statis di UI mungkin mengarah ke `static/templates/upload_template.xlsx` — **per-dataset generator belum ada** (`services/template_service.py` masih rencana).

Rekomendasi batas modul (agen `architecture-strategist`): katalog dataset hanya deklaratif; parser hanya mekanik long-row; orkestrasi di `upload_flow` / `upload_preview`; migrasi `dataset_code` + `upload_runs` bertahap.

## Langkah berikut (proses manusia)

1. **Brainstorm / revisi requirement** — wizard pilih dataset, field manual per dataset, perilaku growth metrics (sudah di plan refactor).
2. **`ce:plan` / implementasi** — kunci `source_sheet` string persis (termasuk spasi `Kartu kredit `), tes parser per slug.
3. Opsional: skrip verifikasi berkala yang membandingkan header baris 0–12 workbook master vs `dataset_catalog` (regresi struktur BI).

## Verifikasi ulang

Setelah workbook diperbarui Bank Indonesia, jalankan ulang inspeksi `header=None` + `nrows` dan bandingkan dengan baris matriks di atas sebelum mengubah katalog.
