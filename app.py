# -*- coding: utf-8 -*-
"""Flask ``app`` instance and test-compat re-exports (factory lives in ``application.factory``)."""
from __future__ import annotations

import sys

from application.factory import create_app
from services.validation import allowed_file, validate_metadata

app = create_app(testing="pytest" in sys.modules)

__all__ = [
    "app",
    "create_app",
    "allowed_file",
    "validate_metadata",
]


if __name__ == "__main__":
    import os

    app.run(debug=True, port=int(os.environ.get("FLASK_RUN_PORT", 5000)))
