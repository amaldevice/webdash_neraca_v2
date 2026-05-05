"""Regenerate static/templates/rekap_dataset_long_templates.xlsx from services catalog.

  python scripts/build_rekap_long_templates.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.template_service import write_multi_dataset_reference_workbook

OUT = ROOT / "static" / "templates" / "rekap_dataset_long_templates.xlsx"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_multi_dataset_reference_workbook(OUT, with_sample=True)


if __name__ == "__main__":
    main()
