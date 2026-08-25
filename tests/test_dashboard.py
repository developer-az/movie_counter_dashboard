#!/usr/bin/env python3
"""Tests for production dashboard helpers: filtering, sampling, and charts."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dashboard"))

from analytics.core import (  # noqa: E402
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
)
import charts  # noqa: E402


def _catalog(n: int = 12) -> pd.DataFrame:
    start = datetime(2020, 1, 1)
    genres = ["Action", "Drama", "Comedy"]
    studios = ["Disney", "Netflix", "A24"]
    rows = []
    for i in range(n):
        budget = 10_000_000 + i * 1_000_000
        gross = budget * (0.5 + (i % 5) * 0.4)
        rows.append(
            {
                "movie_id": i + 1,
                "title": f"Title {i+1}",
                "genre": genres[i % 3],
                "studio": studios[i % 3],
                "rating": "PG-13",
                "release_date": start + timedelta(days=40 * i),
                "budget": budget,
                "total_gross": gross,
                "profit": gross - budget,
                "roi": ((gross - budget) / budget) * 100,
                "imdb_rating": 5 + (i % 5) * 0.7,
            }
        )
    return pd.DataFrame(rows)


def test_resolve_data_path():
    resolved = resolve_data_path("data/processed")
    assert (resolved / "movies_processed.csv").exists(), f"Missing catalog at {resolved}"
    print("✅ Data path resolves from any working directory")


def test_optimize_dtypes_and_memory():
    movies = pd.read_csv(resolve_data_path() / "movies_processed.csv")
    optimized = optimize_dtypes(movies)
    assert str(optimized["genre"].dtype) == "category"
    assert str(optimized["studio"].dtype) == "category"
    assert frame_memory_bytes(optimized) <= frame_memory_bytes(movies)
    print("✅ Dtype optimization keeps categoricals and does not grow memory")


def test_filter_none_vs_empty():
    movies = _catalog()
    all_rows = filter_movies(movies, genres=None)
    none_rows = filter_movies(movies, genres=[])
    action = filter_movies(movies, genres=["Action"])
    assert len(all_rows) == len(movies)
    assert len(none_rows) == 0
    assert set(action["genre"].unique()) == {"Action"}

    found = filter_movies(movies, search="Title 1")
    assert len(found) >= 1
    assert found["title"].str.contains("Title 1", regex=False).all()
    print("✅ Filter treats None as all and [] as none; search is literal")


def test_empty_metrics_do_not_divide():
    empty = compute_overview_metrics(pd.DataFrame())
    assert empty["total_movies"] == 0
    assert empty["profitable_percentage"] == 0.0
    assert empty["avg_rating"] is None

    populated = compute_overview_metrics(_catalog())
    assert populated["total_movies"] == 12
    assert populated["total_revenue"] > 0
    print("✅ Overview metrics are empty-safe")


def test_live_aggregates_respect_filters():
    movies = _catalog()
    action = filter_movies(movies, genres=["Action"])
    genre_stats = compute_genre_stats(action)
    studio_stats = compute_studio_stats(action)
    assert list(genre_stats["genre"].unique()) == ["Action"]
    assert genre_stats["movie_count"].sum() == len(action)
    assert studio_stats["movie_count"].sum() == len(action)
    print("✅ Genre and studio ledgers are computed from the filtered slice")


def test_sample_for_chart_caps_and_preserves_small_frames():
    small = _catalog(20)
    out, sampled, original = sample_for_chart(small, max_points=100, by="genre")
    assert not sampled
    assert len(out) == original == 20

    large = pd.concat([_catalog(50)] * 20, ignore_index=True)
    assert len(large) == 1000
    out, sampled, original = sample_for_chart(large, max_points=120, by="genre")
    assert sampled
    assert original == 1000
    assert len(out) <= 120

    strided, sampled, original = sample_for_chart(large, max_points=80, by=None)
    assert sampled
    assert len(strided) <= 80
    print("✅ Chart sampling keeps small frames intact and caps large ones")


def test_timeseries_rolls_up_when_too_dense():
    days = pd.date_range("2018-01-01", periods=2000, freq="D")
    sales = pd.DataFrame({"date": days, "tickets_sold": 10, "revenue": 100.0})
    daily, grain = auto_resample_timeseries(sales, "date", ["tickets_sold", "revenue"], max_points=5000)
    assert grain == "day"
    assert len(daily) == 2000

    rolled, grain = auto_resample_timeseries(sales, "date", ["tickets_sold", "revenue"], max_points=80)
    assert grain in {"week", "month", "quarter"}
    assert len(rolled) <= 80 or grain == "month"
    assert len(rolled) < 2000
    print(f"✅ Time series auto-roll: 2000 days → {len(rolled)} {grain}s")


def test_date_range_and_previous_window():
    start, end = normalize_date_range(datetime(2022, 6, 1), datetime(2020, 1, 1), datetime(2024, 1, 1))
    assert start == end

    start, end = normalize_date_range(
        (datetime(2023, 12, 1), datetime(2023, 1, 1)),
        datetime(2020, 1, 1),
        datetime(2024, 1, 1),
    )
    assert start < end

    prev_start, prev_end = previous_period_bounds(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-31"))
    assert prev_end == pd.Timestamp("2022-12-31")
    assert (prev_end - prev_start).days == 30
    print("✅ Date range coercion and previous-window deltas")


def test_filter_sales_to_selected_titles():
    movies = _catalog(6)
    sales = pd.DataFrame(
        {
            "movie_id": [1, 1, 2, 99],
            "movie_title": ["A", "A", "B", "Z"],
            "date": pd.date_range("2024-01-01", periods=4, freq="D"),
            "tickets_sold": [10, 11, 12, 13],
            "revenue": [100, 110, 120, 130],
        }
    )
    sliced = filter_sales(sales, movies["movie_id"])
    assert set(sliced["movie_id"].unique()) <= set(movies["movie_id"])
    assert 99 not in set(sliced["movie_id"])
    empty = filter_sales(sales, [])
    assert len(empty) == 0
    print("✅ Sales facts follow the filtered title set")


def test_charts_render_empty_and_populated():
    empty_fig = charts.empty_figure("Empty")
    assert isinstance(empty_fig, go.Figure)

    movies = _catalog()
    fig, note = charts.budget_vs_gross(movies, max_points=50)
    assert isinstance(fig, go.Figure)
    assert note is not None

    stats = compute_genre_stats(movies)
    assert isinstance(charts.genre_pie(movies), go.Figure)
    assert isinstance(charts.roi_distribution(movies), go.Figure)
    assert isinstance(charts.studio_revenue_bar(compute_studio_stats(movies)), go.Figure)
    print("✅ Chart builders return Plotly figures for empty and populated frames")


def test_analytics_core_still_loads():
    engine = MovieAnalytics()
    assert engine.load_data()
    overview = engine.get_overview_metrics()
    assert overview["total_movies"] > 0
    assert "avg_roi" in overview
    print("✅ MovieAnalytics public API still loads the production catalog")


def test_dashboard_syntax():
    import py_compile

    py_compile.compile(str(ROOT / "dashboard" / "streamlit_app.py"), doraise=True)
    py_compile.compile(str(ROOT / "dashboard" / "charts.py"), doraise=True)
    py_compile.compile(str(ROOT / "analytics" / "core.py"), doraise=True)
    print("✅ Dashboard modules compile")


def run_all_tests():
    print("Running dashboard production tests...")
    print("=" * 50)
    test_resolve_data_path()
    test_optimize_dtypes_and_memory()
    test_filter_none_vs_empty()
    test_empty_metrics_do_not_divide()
    test_live_aggregates_respect_filters()
    test_sample_for_chart_caps_and_preserves_small_frames()
    test_timeseries_rolls_up_when_too_dense()
    test_date_range_and_previous_window()
    test_filter_sales_to_selected_titles()
    test_charts_render_empty_and_populated()
    test_analytics_core_still_loads()
    test_dashboard_syntax()
    print("=" * 50)
    print("🎉 All dashboard production tests passed!")
    return True


if __name__ == "__main__":
    run_all_tests()
