"""Katalog dataset REKAP BI untuk upload/input berbasis sheet (Fase 1 refactor)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, Mapping

TableType = Literal["one_way", "two_way", "three_way"]
TimePeriodMode = Literal["monthly", "quarterly", "yearly"]
TemplateMode = Literal["long"]


@dataclass(frozen=True, slots=True)
class DatasetDefinition:
    slug: str
    label: str
    source_sheet: str
    table_type: TableType
    time_period_mode: TimePeriodMode
    required_template_headers: tuple[str, ...]
    manual_form_fields: tuple[str, ...]
    template_mode: TemplateMode
    enabled_for_upload: bool
    enabled_for_manual: bool
    sample_rows: tuple[tuple[object, ...], ...]


_DATASETS: Final[tuple[DatasetDefinition, ...]] = (
    DatasetDefinition(
        slug="pinjaman",
        label="Pinjaman",
        source_sheet="pinjaman",
        table_type="three_way",
        time_period_mode="monthly",
        required_template_headers=(
            "kelompok_bank",
            "kelompok_pinjaman",
            "lapangan_usaha",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        manual_form_fields=(
            "kelompok_bank",
            "kelompok_pinjaman",
            "lapangan_usaha",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        template_mode="long",
        enabled_for_upload=True,
        enabled_for_manual=True,
        sample_rows=(
            (
                "Bank Pemerintah dan Bank Pembangunan Daerah",
                "Pinjaman Berdasarkan Lapangan Usaha",
                "Pertanian, Kehutanan & Perikanan",
                2022,
                4,
                "realisasi",
                993372.628453,
            ),
            (
                "Bank Pemerintah dan Bank Pembangunan Daerah",
                "Pinjaman Berdasarkan Lapangan Usaha",
                "Pertambangan Dan Penggalian",
                2022,
                4,
                "realisasi",
                16050.265891,
            ),
        ),
    ),
    DatasetDefinition(
        slug="simpanan",
        label="Simpanan",
        source_sheet="simpanan",
        table_type="three_way",
        time_period_mode="monthly",
        required_template_headers=(
            "kelompok_jenis_simpanan",
            "produk_simpanan",
            "rentang_nominal",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        manual_form_fields=(
            "kelompok_jenis_simpanan",
            "produk_simpanan",
            "rentang_nominal",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        template_mode="long",
        enabled_for_upload=True,
        enabled_for_manual=True,
        sample_rows=(
            ("Rupiah", "Giro", "0 - 10 juta", 2022, 1, "realisasi", 8865.261165),
            ("Rupiah", "Giro", "> 10 - 100 juta", 2022, 1, "realisasi", 48297.513338),
        ),
    ),
    DatasetDefinition(
        slug="ecommerce",
        label="E-commerce (metode pembayaran)",
        source_sheet="ecommerce",
        table_type="two_way",
        time_period_mode="quarterly",
        required_template_headers=("metode_pembayaran", "tahun", "triwulan", "metric_name", "nilai"),
        manual_form_fields=("metode_pembayaran", "tahun", "triwulan", "metric_name", "nilai"),
        template_mode="long",
        enabled_for_upload=True,
        enabled_for_manual=True,
        sample_rows=(
            ("COD/Tunai", 2020, 1, "realisasi", 10679.82),
            ("e-Money", 2021, 2, "realisasi", 28800.43),
        ),
    ),
    DatasetDefinition(
        slug="atm",
        label="ATM / Debet",
        source_sheet="ATM",
        table_type="two_way",
        time_period_mode="monthly",
        required_template_headers=(
            "jenis_transaksi",
            "jenis_nilai",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        manual_form_fields=(
            "jenis_transaksi",
            "jenis_nilai",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        template_mode="long",
        enabled_for_upload=True,
        enabled_for_manual=True,
        sample_rows=(
            ("Tunai", "volume", 2018, 9, "realisasi", 487354),
            ("Tunai", "nominal", 2018, 9, "realisasi", 338447.94678296254),
        ),
    ),
    DatasetDefinition(
        slug="kartu_kredit",
        label="Kartu kredit",
        source_sheet="Kartu kredit ",
        table_type="two_way",
        time_period_mode="monthly",
        required_template_headers=(
            "jenis_transaksi",
            "jenis_nilai",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        manual_form_fields=(
            "jenis_transaksi",
            "jenis_nilai",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        template_mode="long",
        enabled_for_upload=True,
        enabled_for_manual=True,
        sample_rows=(
            ("Tunai", "volume", 2018, 9, "realisasi", 254),
            ("Tunai", "nominal", 2018, 9, "realisasi", 309.71613361920623),
        ),
    ),
    DatasetDefinition(
        slug="uang_elektronik",
        label="Uang elektronik",
        source_sheet="UANG ELEKTRONIK",
        table_type="two_way",
        time_period_mode="monthly",
        required_template_headers=(
            "jenis_transaksi",
            "jenis_nilai",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        manual_form_fields=(
            "jenis_transaksi",
            "jenis_nilai",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        template_mode="long",
        enabled_for_upload=True,
        enabled_for_manual=True,
        sample_rows=(
            ("BELANJA", "volume", 2019, 10, "realisasi", 117427),
            ("BELANJA", "nominal", 2019, 10, "realisasi", 7457.595445711226),
        ),
    ),
    DatasetDefinition(
        slug="indikator_sekda_bi",
        label="Indikator sekda BI",
        source_sheet="Indikator sekda BI",
        table_type="three_way",
        time_period_mode="monthly",
        required_template_headers=(
            "no_urut",
            "indikator",
            "subindikator",
            "satuan",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        manual_form_fields=(
            "no_urut",
            "indikator",
            "subindikator",
            "satuan",
            "tahun",
            "bulan",
            "metric_name",
            "nilai",
        ),
        template_mode="long",
        enabled_for_upload=True,
        enabled_for_manual=True,
        sample_rows=(
            ("", "Simpanan", "- Giro", "Rp. Juta", 2010, 1, "realisasi", 300933),
            ("", "Simpanan", "- Tabungan", "Rp. Juta", 2010, 1, "realisasi", 875826),
        ),
    ),
)

_BY_SLUG: Final[Mapping[str, DatasetDefinition]] = {d.slug: d for d in _DATASETS}


def list_dataset_slugs() -> list[str]:
    return [d.slug for d in _DATASETS]


def iter_datasets() -> tuple[DatasetDefinition, ...]:
    return _DATASETS


def get_dataset(slug: str) -> DatasetDefinition:
    if slug not in _BY_SLUG:
        raise KeyError(f"Dataset tidak dikenal: {slug!r}. Slug valid: {list(_BY_SLUG)}")
    return _BY_SLUG[slug]


def get_dataset_or_none(slug: str) -> DatasetDefinition | None:
    return _BY_SLUG.get(slug)


def normalize_dataset_code(slug: str | None) -> str:
    """Kode persistensi: slug dataset terpilih, atau string kosong untuk legacy / generik."""
    return (slug or "").strip()


_INVALID_EXCEL_SHEET_CHARS = frozenset("[]:*?/\\")


def dataset_workbook_sheet_title(d: DatasetDefinition) -> str:
    """Judul lembar Excel aman (≤31) untuk template unduhan — selaras lembar sumber BI."""
    base = (d.source_sheet or "").strip() or (d.slug or "").strip() or "data"
    cleaned = "".join("_" if c in _INVALID_EXCEL_SHEET_CHARS else c for c in base).strip() or (d.slug or "data")
    return cleaned[:31]


def dataset_sheet_read_candidates(d: DatasetDefinition) -> tuple[str, ...]:
    """Urutan nama lembar untuk dibuka: master BI, judul template, slug (file lama)."""
    seen: set[str] = set()
    out: list[str] = []
    for n in (
        d.source_sheet,
        d.source_sheet.strip(),
        dataset_workbook_sheet_title(d),
        (d.slug or "")[:31],
    ):
        if n and str(n) not in seen:
            seen.add(str(n))
            out.append(str(n))
    return tuple(out)


def datasets_for_template_context() -> list[dict[str, str | bool]]:
    """Konteks Jinja: daftar dataset untuk dropdown / tautan template."""
    return [
        {
            "slug": d.slug,
            "label": d.label,
            "time_period_mode": d.time_period_mode,
            "source_sheet": d.source_sheet,
            "enabled_for_upload": d.enabled_for_upload,
            "enabled_for_manual": d.enabled_for_manual,
        }
        for d in _DATASETS
        if d.enabled_for_upload or d.enabled_for_manual
    ]
