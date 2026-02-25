from typing import Dict

from models import (
    get_aggregated_cards,
    get_latest_metadata,
    load_cached_summary,
    save_aggregated_summary,
)


def refresh_aggregated_summary() -> Dict:
    latest = get_latest_metadata()
    cards = get_aggregated_cards()
    summary = {"latest": latest, "cards": cards}
    save_aggregated_summary(summary)
    return summary


def fetch_aggregated_summary() -> Dict:
    cached = load_cached_summary()
    if cached:
        return cached
    return refresh_aggregated_summary()
