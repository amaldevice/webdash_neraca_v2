# -*- coding: utf-8 -*-
"""Guardrails for ``tests/simple_tests/functional_tests/pytest.ini`` (GitHub #65)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNC_DIR = ROOT / "tests" / "simple_tests" / "functional_tests"
INI_PATH = FUNC_DIR / "pytest.ini"


def test_functional_tests_pytest_ini_uses_pytest_section():
    text = INI_PATH.read_text(encoding="utf-8")
    assert "[pytest]" in text
    assert "[tool:pytest]" not in text


def test_pytest_reads_ini_when_invoked_from_functional_tests_cwd():
    """``[pytest]`` addopts (e.g. ``--strict-markers``) apply when cwd is the functional suite folder."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=str(FUNC_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
