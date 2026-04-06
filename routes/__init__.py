# -*- coding: utf-8 -*-
"""Register all HTTP routes on a Flask application (preserves endpoint names for url_for)."""
from __future__ import annotations

from flask import Flask

from routes import manage, pages, upload_routes


def register_routes(app: Flask) -> None:
    pages.register(app)
    upload_routes.register(app)
    manage.register(app)
