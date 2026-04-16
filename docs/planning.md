# Planning (sinkron proyek)

**Ringkasan state, peta dokumentasi, panduan unggah/migrasi:** semua ada di **[README_DOCS.md](README_DOCS.md)** — itu sumber utama untuk manusia dan agen.

## Kewajiban saat mengubah perilaku / fitur / bugfix

1. Perbarui **[README_DOCS.md](README_DOCS.md)** — setidaknya bagian **Changelog ringkas** (bullet bertanggal + taut file terkait).
2. Perbarui plan YAML: **[`.cursor/plans/bps_data_management_system_bd94389d.plan.md`](../.cursor/plans/bps_data_management_system_bd94389d.plan.md)** (ikut Git). Bila mengedit salinan di `%USERPROFILE%\.cursor\plans\`, samakan ke file dalam repo.
3. Ikuti [.cursor/rules/planning-&-executing-sync.mdc](../.cursor/rules/planning-&-executing-sync.mdc) (produksi kantor, tanpa rahasia di kode).

Riwayat naratif panjang sebelum konsolidasi 2026-04-17: `git log --follow -p -- docs/planning.md` (dan `docs/refactor-planning.md` jika masih di history).
