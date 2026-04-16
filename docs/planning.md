# Planning (sinkron proyek)

**Ringkasan state, peta dokumentasi, panduan unggah/migrasi:** semua ada di **[README_DOCS.md](README_DOCS.md)** — itu sumber utama untuk manusia dan agen.

## Kewajiban saat mengubah perilaku / fitur / bugfix

1. Perbarui **[README_DOCS.md](README_DOCS.md)** — setidaknya bagian **Changelog ringkas** (bullet bertanggal + taut file terkait).
2. Perbarui plan YAML: **[plans/bps_data_management_system_bd94389d.plan.md](plans/bps_data_management_system_bd94389d.plan.md)** (kanon repo, ikut Git). Salin isi ke `%USERPROFILE%\.cursor\plans\bps_data_management_system_bd94389d.plan.md` bila memakai UI plan Cursor.
3. Ikuti [.cursor/rules/planning-&-executing-sync.mdc](../.cursor/rules/planning-&-executing-sync.mdc) (produksi kantor, tanpa rahasia di kode).

Riwayat naratif panjang sebelum konsolidasi 2026-04-17: `git log --follow -p -- docs/planning.md` (dan `docs/refactor-planning.md` jika masih di history).
