# -*- coding: utf-8 -*-
from __future__ import annotations


def get_period_range_params(
    source,
    start_key: str = "start_period",
    end_key: str = "end_period",
) -> tuple[str | None, str | None]:
    """Extract optional period-range parameters from request-like inputs."""
    start_period = source.get(start_key, "", type=str)
    end_period = source.get(end_key, "", type=str)
    return (
        start_period.strip() if start_period is not None else None,
        end_period.strip() if end_period is not None else None,
    )
