"""Shim: re-export aggregation API for backward compatibility (e.g. ``patch('aggregator.*')``)."""
from services.aggregation import fetch_aggregated_summary, refresh_aggregated_summary

__all__ = ["fetch_aggregated_summary", "refresh_aggregated_summary"]
