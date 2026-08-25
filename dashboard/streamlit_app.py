"""
Movie Industry Analytics — production dashboard.

A single-page, filter-driven workspace. Only the active view is rendered so
aggregations and Plotly traces stay bounded as the catalog grows. Shared
analytics live in ``analytics.core``; this module is presentation.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

import pandas as pd
import streamlit as st

import charts
from analytics.core import (
    MAX_LINE_POINTS,
    MAX_SCATTER_POINTS,
    MAX_SCATTER_POINTS_FAST,
    MovieAnalytics,
    auto_resample_timeseries,
    compute_genre_stats,
    compute_overview_metrics,
    compute_studio_stats,
    filter_movies,
    filter_sales,
    frame_memory_bytes,
    normalize_date_range,
    previous_period_bounds,
    unique_sorted,
)

st.set_page_config(
    page_title="Box Office Intelligence",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

VIEWS = ("Overview", "Genres", "Studios", "Trends", "Sales", "Explorer")
STUDIO_COMPACT_THRESHOLD = 40
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp {
    font-family: "IBM Plex Sans", Inter, system-ui, sans-serif;
}
.block-container {
    padding-top: 1.15rem;
    padding-bottom: 2.4rem;
    max-width: 1440px;
}
div[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.06);
}
div[data-testid="stSidebar"] h1, div[data-testid="stSidebar"] h2, div[data-testid="stSidebar"] h3 {
    letter-spacing: 0.02em;
}
[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(28,38,51,0.95), rgba(16,22,31,0.92));
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 14px 16px 10px 16px;
}
[data-testid="stMetricLabel"] {
    color: #8B9BB0 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-weight: 500;
    font-size: 1.55rem;
}
.hero-kicker {
    color: #F5C542;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 0.15rem;
}
.hero-title {
    font-size: 1.85rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #F4F7FB;
    margin: 0 0 0.25rem 0;
    line-height: 1.2;
}
.hero-sub {
    color: #8B9BB0;
    font-size: 0.95rem;
    margin-bottom: 0.4rem;
}
.insight-banner {
    background: rgba(245, 197, 66, 0.08);
    border: 1px solid rgba(245, 197, 66, 0.22);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    color: #E8EEF6;
    font-size: 0.92rem;
    margin: 0.4rem 0 0.8rem 0;
}
.empty-panel {
    border: 1px dashed rgba(255,255,255,0.12);
    border-radius: 14px;
    padding: 2.4rem 1.5rem;
    text-align: center;
    color: #8B9BB0;
}
.footer-meta {
    color: #6B7C90;
    font-size: 0.8rem;
    margin-top: 1.4rem;
}
hr { border-color: rgba(255,255,255,0.08); }
</style>
"""


def fmt_money(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    amount = float(value)
    magnitude = abs(amount)
    if magnitude >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    if magnitude >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if magnitude >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,.0f}"


def fmt_number(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.0f}"


def fmt_pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.1f}%"


def fmt_rating(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.1f}"


def delta_pct(current: float | None, previous: float | None) -> str | None:
    if current is None or previous in (None, 0) or pd.isna(previous):
        return None
    change = (float(current) - float(previous)) / abs(float(previous)) * 100.0
    return f"{change:+.1f}%"


def memory_label(nbytes: int) -> str:
    if nbytes >= 1_000_000:
        return f"{nbytes / 1_000_000:.1f} MB"
    if nbytes >= 1_000:
        return f"{nbytes / 1_000:.0f} KB"
    return f"{nbytes} B"


@st.cache_data(show_spinner=False, ttl=3600)
def load_catalog() -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    engine = MovieAnalytics()
    if not engine.load_data():
        return None, None
    return engine.movies, engine.sales


def render_empty(message: str) -> None:
    st.markdown(f'<div class="empty-panel">{message}</div>', unsafe_allow_html=True)


def plot(fig, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, config=charts.PLOT_CONFIG, key=key)


def render_overview(movies: pd.DataFrame, scatter_cap: int) -> None:
    genre_stats = compute_genre_stats(movies)
    left, right = st.columns(2)
    fig, note = charts.budget_vs_gross(movies, max_points=scatter_cap)
    with left:
        plot(fig, "ov-scatter")
        if note:
            st.caption(note)
    with right:
        plot(charts.roi_distribution(movies), "ov-roi")

    st.subheader("Lead titles")
    t1, t2 = st.columns(2)
    top_gross = movies.nlargest(10, "total_gross")[["title", "genre", "studio", "total_gross", "imdb_rating"]]
    top_roi = movies.nlargest(10, "roi")[["title", "genre", "studio", "roi", "budget"]]
    with t1:
        st.caption("Highest box office")
        st.dataframe(
            top_gross,
            hide_index=True,
            use_container_width=True,
            column_config={
                "title": st.column_config.TextColumn("Title"),
                "genre": "Genre",
                "studio": "Studio",
                "total_gross": st.column_config.NumberColumn("Box office", format="$%d"),
                "imdb_rating": st.column_config.NumberColumn("IMDb", format="%.1f"),
            },
        )
    with t2:
        st.caption("Highest ROI")
        st.dataframe(
            top_roi,
            hide_index=True,
            use_container_width=True,
            column_config={
                "title": st.column_config.TextColumn("Title"),
                "genre": "Genre",
                "studio": "Studio",
                "roi": st.column_config.NumberColumn("ROI", format="%.1f%%"),
                "budget": st.column_config.NumberColumn("Budget", format="$%d"),
            },
        )

    if not genre_stats.empty:
        lead = genre_stats.iloc[0]
        st.markdown(
            f'<div class="insight-banner"><strong>Read:</strong> {lead["genre"]} leads this slice '
            f"with {fmt_money(lead['total_gross'])} in box office across {int(lead['movie_count'])} titles "
            f"(avg ROI {fmt_pct(lead['avg_roi'])}).</div>",
            unsafe_allow_html=True,
        )


def render_genres(movies: pd.DataFrame) -> None:
    stats = compute_genre_stats(movies)
    if stats.empty:
        render_empty("No genre mix to show for this slice.")
        return

    left, right = st.columns(2)
    with left:
        plot(charts.genre_revenue_treemap(stats), "ge-tree")
    with right:
        plot(charts.roi_by_genre_box(movies), "ge-box")

    b1, b2 = st.columns(2)
    with b1:
        plot(charts.genre_bar(stats, "avg_gross", "Average box office by genre", "Avg box office", money=True), "ge-avg")
    with b2:
        plot(charts.genre_bar(stats, "avg_rating", "Average IMDb by genre", "IMDb"), "ge-rating")

    st.subheader("Genre ledger")
    display = stats.copy()
    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "genre": "Genre",
            "movie_count": st.column_config.NumberColumn("Titles", format="%d"),
            "avg_budget": st.column_config.NumberColumn("Avg budget", format="$%d"),
            "median_budget": st.column_config.NumberColumn("Median budget", format="$%d"),
            "avg_gross": st.column_config.NumberColumn("Avg box office", format="$%d"),
            "median_gross": st.column_config.NumberColumn("Median box office", format="$%d"),
            "total_gross": st.column_config.NumberColumn("Total box office", format="$%d"),
            "avg_rating": st.column_config.NumberColumn("Avg IMDb", format="%.2f"),
            "avg_profit": st.column_config.NumberColumn("Avg profit", format="$%d"),
            "median_profit": st.column_config.NumberColumn("Median profit", format="$%d"),
            "avg_roi": st.column_config.NumberColumn("Avg ROI", format="%.1f%%"),
            "profitable_pct": st.column_config.ProgressColumn("Profitable", min_value=0, max_value=100, format="%.1f%%"),
        },
    )


def render_studios(movies: pd.DataFrame) -> None:
    stats = compute_studio_stats(movies)
    if stats.empty:
        render_empty("No studio mix to show for this slice.")
        return

    left, right = st.columns(2)
    with left:
        plot(charts.studio_revenue_bar(stats), "st-bar")
    with right:
        plot(charts.studio_volume_vs_yield(stats), "st-scatter")

    st.subheader("Studio ledger")
    st.dataframe(
        stats,
        hide_index=True,
        use_container_width=True,
        column_config={
            "studio": "Studio",
            "movie_count": st.column_config.NumberColumn("Titles", format="%d"),
            "avg_budget": st.column_config.NumberColumn("Avg budget", format="$%d"),
            "total_budget": st.column_config.NumberColumn("Total budget", format="$%d"),
            "avg_gross": st.column_config.NumberColumn("Avg box office", format="$%d"),
            "total_gross": st.column_config.NumberColumn("Total box office", format="$%d"),
            "avg_rating": st.column_config.NumberColumn("Avg IMDb", format="%.2f"),
            "avg_roi": st.column_config.NumberColumn("Avg ROI", format="%.1f%%"),
            "profitable_pct": st.column_config.ProgressColumn("Profitable", min_value=0, max_value=100, format="%.1f%%"),
        },
    )


def render_trends(movies: pd.DataFrame, scatter_cap: int) -> None:
    working = movies.copy()
    if "release_year" not in working.columns:
        working["release_year"] = working["release_date"].dt.year

    yearly = (
        working.groupby("release_year", observed=True)
        .agg(titles=("movie_id", "count"), avg_gross=("total_gross", "mean"), avg_rating=("imdb_rating", "mean"))
        .reset_index()
    )
    c1, c2 = st.columns(2)
    with c1:
        plot(charts.yearly_line(yearly, "titles", "Titles released per year", "Titles"), "tr-count")
    with c2:
        plot(charts.yearly_line(yearly, "avg_gross", "Average box office per year", "Avg box office", money=True), "tr-gross")

    fig, note = charts.rating_over_time(working, max_points=scatter_cap)
    plot(fig, "tr-ratings")
    if note:
        st.caption(note)


def render_sales(sales: pd.DataFrame, line_cap: int) -> None:
    if sales is None or sales.empty:
        render_empty("No sales rows for the titles in this slice.")
        return

    series, grain = auto_resample_timeseries(sales, "date", ["tickets_sold", "revenue"], max_points=line_cap)
    c1, c2 = st.columns(2)
    with c1:
        plot(charts.sales_line(series, "tickets_sold", "Ticket volume", "Tickets", grain), "sa-tickets")
    with c2:
        plot(charts.sales_line(series, "revenue", "Box office from tickets", "Revenue", grain, money=True), "sa-rev")
    if grain != "day":
        st.caption(f"Series auto-rolled to {grain}s because the daily grain exceeded {line_cap:,} points.")

    weekend_source = sales.copy()
    if "is_weekend" not in weekend_source.columns:
        weekend_source["is_weekend"] = weekend_source["date"].dt.weekday >= 5
    weekend = (
        weekend_source.groupby("is_weekend", observed=True)
        .agg(tickets_sold=("tickets_sold", "mean"), revenue=("revenue", "mean"))
        .reset_index()
    )
    weekend["day_type"] = weekend["is_weekend"].map({True: "Weekend", False: "Weekday", 1: "Weekend", 0: "Weekday"})
    w1, w2 = st.columns(2)
    with w1:
        plot(charts.weekend_bar(weekend, "tickets_sold", "Avg tickets · weekend vs weekday", "Tickets"), "sa-wk-t")
    with w2:
        plot(charts.weekend_bar(weekend, "revenue", "Avg revenue · weekend vs weekday", "Revenue"), "sa-wk-r")

    top = (
        sales.groupby("movie_title", observed=True)["tickets_sold"]
        .sum()
        .nlargest(15)
        .reset_index()
    )
    plot(charts.top_titles_bar(top, "tickets_sold", "movie_title", "Top 15 titles by tickets"), "sa-top")


def render_explorer(movies: pd.DataFrame) -> None:
    st.caption("Full filtered catalog. Sort, search, and export without drawing a chart for every row.")
    visible_cols = [
        "title",
        "genre",
        "studio",
        "rating",
        "release_date",
        "budget",
        "total_gross",
        "profit",
        "roi",
        "imdb_rating",
        "runtime_minutes",
    ]
    present = [c for c in visible_cols if c in movies.columns]
    st.dataframe(
        movies[present],
        hide_index=True,
        use_container_width=True,
        height=560,
        column_config={
            "title": st.column_config.TextColumn("Title", width="medium"),
            "genre": "Genre",
            "studio": "Studio",
            "rating": "MPAA",
            "release_date": st.column_config.DateColumn("Released"),
            "budget": st.column_config.NumberColumn("Budget", format="$%d"),
            "total_gross": st.column_config.NumberColumn("Box office", format="$%d"),
            "profit": st.column_config.NumberColumn("Profit", format="$%d"),
            "roi": st.column_config.NumberColumn("ROI", format="%.1f%%"),
            "imdb_rating": st.column_config.ProgressColumn("IMDb", min_value=0, max_value=10, format="%.1f"),
            "runtime_minutes": st.column_config.NumberColumn("Runtime", format="%d min"),
        },
    )
    csv = movies[present].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download this slice as CSV",
        data=csv,
        file_name="box_office_slice.csv",
        mime="text/csv",
        use_container_width=False,
    )


def main() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)

    movies, sales = load_catalog()
    if movies is None or movies.empty:
        st.error("Processed data files were not found. Run `python3 scripts/generate_data.py` and `python3 scripts/data_processing.py` from the `scripts` directory.")
        st.stop()

    if "filter_epoch" not in st.session_state:
        st.session_state.filter_epoch = 0
    epoch = st.session_state.filter_epoch

    min_date = pd.Timestamp(movies["release_date"].min()).date()
    max_date = pd.Timestamp(movies["release_date"].max()).date()
    genres_all = unique_sorted(movies["genre"])
    studios_all = unique_sorted(movies["studio"])
    ratings_all = unique_sorted(movies["rating"])
    budget_hi = int(max(movies["budget"].max() / 1_000_000, 1))
    rating_lo = float(movies["imdb_rating"].min())
    rating_hi = float(movies["imdb_rating"].max())

    with st.sidebar:
        st.markdown("### Workspace")
        st.caption("Filters apply to every view. Only the active view is computed.")
        if st.button("Reset filters", use_container_width=True, key="reset-filters"):
            st.session_state.filter_epoch += 1
            st.rerun()

        search = st.text_input("Search titles", placeholder="Partial title…", key=f"search-{epoch}")
        date_value = st.date_input(
            "Release window",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"dates-{epoch}",
        )
        selected_genres = st.multiselect("Genres", options=genres_all, default=genres_all, key=f"genres-{epoch}")

        if len(studios_all) > STUDIO_COMPACT_THRESHOLD:
            selected_studios = st.multiselect(
                "Studios",
                options=studios_all,
                default=[],
                key=f"studios-{epoch}",
                help="Leave empty to include every studio. Defaults stay empty once the catalog is large.",
            )
        else:
            selected_studios = st.multiselect(
                "Studios", options=studios_all, default=studios_all, key=f"studios-{epoch}"
            )

        selected_ratings = st.multiselect("MPAA rating", options=ratings_all, default=ratings_all, key=f"mpaa-{epoch}")
        budget_range = st.slider(
            "Budget (USD millions)",
            min_value=0,
            max_value=budget_hi,
            value=(0, budget_hi),
            step=max(1, budget_hi // 50),
            key=f"budget-{epoch}",
        )
        imdb_range = st.slider(
            "IMDb rating",
            min_value=0.0,
            max_value=10.0,
            value=(max(0.0, round(rating_lo, 1)), min(10.0, round(rating_hi, 1))),
            step=0.1,
            key=f"imdb-{epoch}",
        )

        st.markdown("#### Chart fidelity")
        fidelity = st.radio(
            "Chart fidelity",
            options=("Auto", "Performance", "High fidelity"),
            index=0,
            label_visibility="collapsed",
            key=f"fidelity-{epoch}",
            help="Performance caps scatter traces and rolls up long time series. High fidelity raises those caps for smaller slices.",
        )

        mem = frame_memory_bytes(movies) + frame_memory_bytes(sales)
        st.markdown("#### Catalog")
        st.caption(
            f"{len(movies):,} titles · {0 if sales is None else len(sales):,} sales rows · {memory_label(mem)} in memory"
        )
        st.caption("Scatter traces downsample above 4,000 points. Time series roll up past 1,500 grains.")

    date_start, date_end = normalize_date_range(date_value, min_date, max_date)
    # Large catalogs: empty studio widget means "all" so we never default-select hundreds of values.
    studio_filter = selected_studios
    if len(studios_all) > STUDIO_COMPACT_THRESHOLD and not selected_studios:
        studio_filter = None

    filter_kwargs = dict(
        date_start=date_start,
        date_end=date_end,
        genres=selected_genres,
        studios=studio_filter,
        ratings=selected_ratings,
        budget_min=budget_range[0] * 1_000_000,
        budget_max=budget_range[1] * 1_000_000,
        imdb_min=imdb_range[0],
        imdb_max=imdb_range[1],
        search=search,
    )
    filtered = filter_movies(movies, **filter_kwargs)

    prev_start, prev_end = previous_period_bounds(date_start, date_end)
    previous = filter_movies(
        movies,
        **{**filter_kwargs, "date_start": prev_start, "date_end": prev_end},
    )

    current_kpis = compute_overview_metrics(filtered)
    previous_kpis = compute_overview_metrics(previous)

    if fidelity == "Performance":
        scatter_cap, line_cap = MAX_SCATTER_POINTS_FAST, 750
    elif fidelity == "High fidelity":
        scatter_cap, line_cap = 12_000, 5_000
    else:
        scatter_cap, line_cap = MAX_SCATTER_POINTS, MAX_LINE_POINTS

    st.markdown('<div class="hero-kicker">Production analytics</div>', unsafe_allow_html=True)
    st.markdown('<p class="hero-title">Box Office Intelligence</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="hero-sub">{fmt_number(current_kpis["total_movies"])} titles in view · '
        f'{date_start.date()} → {date_end.date()} · deltas vs the prior window of equal length</p>',
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Titles", fmt_number(current_kpis["total_movies"]), delta=delta_pct(current_kpis["total_movies"], previous_kpis["total_movies"]))
    k2.metric(
        "Box office",
        fmt_money(current_kpis["total_revenue"]),
        delta=delta_pct(current_kpis["total_revenue"], previous_kpis["total_revenue"]),
        help="Sum of domestic + international gross in the current slice.",
    )
    k3.metric("Avg IMDb", fmt_rating(current_kpis["avg_rating"]), delta=delta_pct(current_kpis["avg_rating"], previous_kpis["avg_rating"]))
    k4.metric(
        "Profitable",
        fmt_pct(current_kpis["profitable_percentage"]),
        delta=delta_pct(current_kpis["profitable_percentage"], previous_kpis["profitable_percentage"]),
        help="Share of titles where box office exceeds production budget.",
    )
    k5.metric("Avg ROI", fmt_pct(current_kpis["avg_roi"]), delta=delta_pct(current_kpis["avg_roi"], previous_kpis["avg_roi"]))

    view = st.radio("View", options=VIEWS, horizontal=True, label_visibility="collapsed", key="workspace-view")

    if filtered.empty:
        render_empty("No titles match the current filters. Reset the sidebar or widen the release window.")
    elif view == "Overview":
        render_overview(filtered, scatter_cap)
    elif view == "Genres":
        render_genres(filtered)
    elif view == "Studios":
        render_studios(filtered)
    elif view == "Trends":
        render_trends(filtered, scatter_cap)
    elif view == "Sales":
        sliced_sales = filter_sales(sales, filtered["movie_id"])
        render_sales(sliced_sales, line_cap)
    else:
        render_explorer(filtered)

    st.markdown(
        f'<p class="footer-meta">{len(movies):,} titles loaded · '
        f'{0 if sales is None else len(sales):,} sales facts · '
        f'{memory_label(frame_memory_bytes(movies) + frame_memory_bytes(sales))} resident · '
        f'scatter cap {scatter_cap:,} · series cap {line_cap:,} points · '
        f'WebGL traces · live aggregates (not static CSVs)</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
