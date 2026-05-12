# -*- coding: utf-8 -*-
"""POST /upload guards: CSRF + optional per-client rate limit (isolated from view wiring)."""
from __future__ import annotations

import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Literal

from flask import current_app, request, session

_BlockReason = Literal["", "csrf", "rate_limit"]


@dataclass(frozen=True, slots=True)
class UploadRateLimitDecision:
    """Outcome of rate-limit check only (runs before form body parsing)."""

    allowed: bool
    window_seconds: int
    max_requests: int


@dataclass(frozen=True, slots=True)
class UploadCsrfDecision:
    """Outcome of CSRF check (runs after form values are parsed for error UX)."""

    allowed: bool


_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_STATE: dict[str, deque[float]] = defaultdict(deque)


def _validate_upload_csrf_token() -> bool:
    expected = session.get("_upload_csrf_token")
    provided = request.form.get("csrf_token", "")
    if not expected or not provided:
        return False
    return secrets.compare_digest(str(expected), str(provided))


def upload_client_key() -> str:
    client_key = session.get("_upload_client_id")
    if not isinstance(client_key, str) or not client_key.strip():
        client_key = secrets.token_urlsafe(16)
        session["_upload_client_id"] = client_key
    return client_key


def evaluate_upload_rate_limit() -> UploadRateLimitDecision:
    """Per-client sliding window; call on POST /upload before reading multipart form."""
    if request.method != "POST" or request.path != "/upload":
        return UploadRateLimitDecision(allowed=True, window_seconds=60, max_requests=0)

    max_requests = int(current_app.config.get("UPLOAD_RATE_LIMIT_MAX_REQUESTS", 0))
    window_seconds = int(current_app.config.get("UPLOAD_RATE_LIMIT_WINDOW_SECONDS", 60))
    if max_requests <= 0:
        return UploadRateLimitDecision(allowed=True, window_seconds=window_seconds, max_requests=max_requests)

    key = upload_client_key()
    now = time.monotonic()
    with _RATE_LIMIT_LOCK:
        bucket = _RATE_LIMIT_STATE[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= max_requests:
            return UploadRateLimitDecision(
                allowed=False, window_seconds=window_seconds, max_requests=max_requests
            )
        bucket.append(now)
    return UploadRateLimitDecision(allowed=True, window_seconds=window_seconds, max_requests=max_requests)


def evaluate_upload_csrf() -> UploadCsrfDecision:
    """Validate form CSRF token against session (after form fields are parsed)."""
    return UploadCsrfDecision(allowed=_validate_upload_csrf_token())
