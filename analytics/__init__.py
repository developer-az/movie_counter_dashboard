"""
Analytics Core Module

Shared analytics functions for movie industry data analysis.
Used by both dashboard and terminal interfaces.
"""

from .core import (
    MovieAnalytics,
    auto_resample_timeseries,
    compute_genre_stats,
    compute_overview_metrics,
    compute_studio_stats,
    filter_movies,
    filter_sales,
    frame_memory_bytes,
    normalize_date_range,
    optimize_dtypes,
    previous_period_bounds,
    resolve_data_path,
    sample_for_chart,
    unique_sorted,
)

__all__ = [
    "MovieAnalytics",
    "auto_resample_timeseries",
    "compute_genre_stats",
    "compute_overview_metrics",
    "compute_studio_stats",
    "filter_movies",
    "filter_sales",
    "frame_memory_bytes",
    "normalize_date_range",
    "optimize_dtypes",
    "previous_period_bounds",
    "resolve_data_path",
    "sample_for_chart",
    "unique_sorted",
]
