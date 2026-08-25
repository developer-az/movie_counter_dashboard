"""
Movie Industry Analytics Dashboard

Interactive workspace for published box-office figures: filters, KPIs, and the
original five analysis tabs plus a searchable catalog. Shared analytics live in
``analytics.core``.
"""

from __future__ import annotations

import inspect
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
    MovieAnalytics,
    auto_resample_timeseries,
    compute_genre_stats,
    compute_overview_metrics,
    compute_studio_stats,
    filter_movies,
    filter_sales,
    normalize_date_range,
    unique_sorted,
)

st.set_page_config(
    page_title="Movie Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _width_kwargs(fn, stretch: bool = True) -> dict:
    try:
        if "width" in inspect.signature(fn).parameters:
            return {"width": "stretch" if stretch else "content"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": stretch}


APP_CSS = """
<style>
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }
[data-testid="stMetric"] {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #E11D48;
    border-radius: 8px;
    padding: 0.85rem 1rem;
}
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { height: 48px; padding: 0 18px; }
.source-note { color: #64748B; font-size: 0.9rem; margin: 0.2rem 0 0.8rem 0; }
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
    return f"{float(value):.1f}/10"


@st.cache_data(show_spinner=False, ttl=3600)
def load_catalog() -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    engine = MovieAnalytics()
    if not engine.load_data():
        return None, None
    return engine.movies, engine.sales


def plot(fig, key: str) -> None:
    st.plotly_chart(fig, config=charts.PLOT_CONFIG, key=key, **_width_kwargs(st.plotly_chart))


def money_table(df: pd.DataFrame, column_config: dict) -> None:
    st.dataframe(df, hide_index=True, **_width_kwargs(st.dataframe), column_config=column_config)


def show_overview_tab(movies: pd.DataFrame) -> None:
    left, right = st.columns(2)
    fig, note = charts.budget_vs_gross(movies, max_points=MAX_SCATTER_POINTS)
    with left:
        plot(fig, "ov-scatter")
        if note:
            st.caption(note)
    with right:
        plot(charts.roi_distribution(movies), "ov-roi")
        st.caption("Histogram clipped to the 5th–95th percentile so a few mega-hits do not squash the rest. Red = 0% ROI.")

    st.subheader("🏆 Top Performing Movies")
    t1, t2 = st.columns(2)
    with t1:
        st.write("**Top 10 by Total Gross**")
        top_gross = movies.nlargest(10, "total_gross")[["title", "genre", "studio", "total_gross", "imdb_rating"]]
        money_table(
            top_gross,
            {
                "title": st.column_config.TextColumn("Title"),
                "genre": "Genre",
                "studio": "Studio",
                "total_gross": st.column_config.NumberColumn("Box office", format="$%d"),
                "imdb_rating": st.column_config.NumberColumn("IMDb", format="%.1f"),
            },
        )
    with t2:
        st.write("**Top 10 by ROI**")
        top_roi = movies.nlargest(10, "roi")[["title", "genre", "studio", "roi", "budget"]]
        money_table(
            top_roi,
            {
                "title": st.column_config.TextColumn("Title"),
                "genre": "Genre",
                "studio": "Studio",
                "roi": st.column_config.NumberColumn("ROI", format="%.1f%%"),
                "budget": st.column_config.NumberColumn("Budget", format="$%d"),
            },
        )
        st.caption("Highest ROI is usually a cheap breakout (Blair Witch, Paranormal Activity), not the biggest movie.")


def show_genre_analysis(movies: pd.DataFrame) -> None:
    stats = compute_genre_stats(movies)
    if stats.empty:
        st.info("No titles match the current filters.")
        return

    c1, c2 = st.columns(2)
    with c1:
        plot(charts.genre_pie(movies), "ge-pie")
    with c2:
        plot(charts.genre_avg_revenue_bar(stats), "ge-avg")

    plot(charts.roi_by_genre_box(movies), "ge-box")
    st.caption("Box plot shows the full ROI spread, not just the average — useful because a few breakout hits pull the mean up.")

    st.subheader("📊 Detailed Genre Statistics")
    money_table(
        stats,
        {
            "genre": "Genre",
            "movie_count": st.column_config.NumberColumn("Movies", format="%d"),
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


def show_studio_analysis(movies: pd.DataFrame) -> None:
    stats = compute_studio_stats(movies)
    if stats.empty:
        st.info("No titles match the current filters.")
        return

    c1, c2 = st.columns(2)
    with c1:
        plot(charts.studio_revenue_bar(stats), "st-bar")
    with c2:
        plot(charts.studio_volume_vs_yield(stats), "st-scatter")
        st.caption("Bubble size is studio total box office. Hover a point to see the studio name.")

    st.subheader("🏢 Studio Performance Statistics")
    money_table(
        stats,
        {
            "studio": "Studio",
            "movie_count": st.column_config.NumberColumn("Movies", format="%d"),
            "avg_budget": st.column_config.NumberColumn("Avg budget", format="$%d"),
            "total_budget": st.column_config.NumberColumn("Total budget", format="$%d"),
            "avg_gross": st.column_config.NumberColumn("Avg box office", format="$%d"),
            "total_gross": st.column_config.NumberColumn("Total box office", format="$%d"),
            "avg_rating": st.column_config.NumberColumn("Avg IMDb", format="%.2f"),
            "avg_roi": st.column_config.NumberColumn("Avg ROI", format="%.1f%%"),
            "profitable_pct": st.column_config.ProgressColumn("Profitable", min_value=0, max_value=100, format="%.1f%%"),
        },
    )


def show_trends_analysis(movies: pd.DataFrame) -> None:
    working = movies.copy()
    if "release_year" not in working.columns:
        working["release_year"] = pd.to_datetime(working["release_date"]).dt.year

    yearly = (
        working.groupby("release_year", observed=True)
        .agg(titles=("movie_id", "count"), avg_gross=("total_gross", "mean"))
        .reset_index()
    )
    c1, c2 = st.columns(2)
    with c1:
        plot(charts.yearly_line(yearly, "titles", "Number of Movies Released per Year", "Movies"), "tr-count")
    with c2:
        plot(
            charts.yearly_line(yearly, "avg_gross", "Average Gross Revenue per Year", "Avg box office", money=True),
            "tr-gross",
        )

    fig, note = charts.rating_over_time(working, max_points=MAX_SCATTER_POINTS)
    plot(fig, "tr-ratings")
    if note:
        st.caption(note)


def show_sales_analysis(sales: pd.DataFrame, n_modeled: int) -> None:
    if sales is None or sales.empty:
        st.info(
            "No modeled ticket runs in this slice. Daily sales are built for the 100 highest domestic-gross titles; "
            "try widening filters or opening the full catalog."
        )
        return

    st.caption(
        f"8-week theatrical model for {sales['movie_id'].nunique()} of the catalog's top domestic titles "
        f"(up to {n_modeled} modeled). Daily revenue is scaled to each film's reported domestic gross, "
        "so weekend vs weekday shape is preserved and totals are not random."
    )

    series, grain = auto_resample_timeseries(sales, "date", ["tickets_sold", "revenue"], max_points=MAX_LINE_POINTS)
    c1, c2 = st.columns(2)
    with c1:
        plot(charts.sales_line(series, "tickets_sold", "Daily Ticket Sales Over Time", "Tickets", grain), "sa-tix")
    with c2:
        plot(charts.sales_line(series, "revenue", "Daily Revenue Over Time", "Revenue", grain, money=True), "sa-rev")

    weekend_source = sales.copy()
    if "is_weekend" not in weekend_source.columns:
        weekend_source["is_weekend"] = pd.to_datetime(weekend_source["date"]).dt.weekday >= 5
    weekend = (
        weekend_source.groupby("is_weekend", observed=True)
        .agg(tickets_sold=("tickets_sold", "mean"), revenue=("revenue", "mean"))
        .reset_index()
    )
    weekend["day_type"] = weekend["is_weekend"].map({True: "Weekend", False: "Weekday", 1: "Weekend", 0: "Weekday"})
    w1, w2 = st.columns(2)
    with w1:
        plot(charts.weekend_bar(weekend, "tickets_sold", "Average Tickets Sold: Weekend vs Weekday", "Avg tickets"), "sa-wk-t")
    with w2:
        plot(
            charts.weekend_bar(weekend, "revenue", "Average Revenue: Weekend vs Weekday", "Avg revenue", money=True),
            "sa-wk-r",
        )

    top = sales.groupby("movie_title", observed=True)["tickets_sold"].sum().nlargest(15).reset_index()
    plot(charts.top_titles_bar(top, "tickets_sold", "movie_title", "Top 15 Movies by Total Ticket Sales"), "sa-top")


def show_catalog(movies: pd.DataFrame) -> None:
    st.caption("Searchable slice of the current filters. Sort any column; download exports the rows you see.")
    present = [
        c
        for c in [
            "title",
            "genre",
            "studio",
            "rating",
            "release_date",
            "budget",
            "domestic_gross",
            "international_gross",
            "total_gross",
            "profit",
            "roi",
            "imdb_rating",
            "runtime_minutes",
        ]
        if c in movies.columns
    ]
    money_table(
        movies[present],
        {
            "title": st.column_config.TextColumn("Title", width="medium"),
            "genre": "Genre",
            "studio": "Studio",
            "rating": "MPAA",
            "release_date": st.column_config.DateColumn("Released"),
            "budget": st.column_config.NumberColumn("Budget", format="$%d"),
            "domestic_gross": st.column_config.NumberColumn("Domestic", format="$%d"),
            "international_gross": st.column_config.NumberColumn("International", format="$%d"),
            "total_gross": st.column_config.NumberColumn("Worldwide", format="$%d"),
            "profit": st.column_config.NumberColumn("Profit", format="$%d"),
            "roi": st.column_config.NumberColumn("ROI", format="%.1f%%"),
            "imdb_rating": st.column_config.NumberColumn("IMDb", format="%.1f"),
            "runtime_minutes": st.column_config.NumberColumn("Runtime", format="%d min"),
        },
    )
    st.download_button(
        "Download this slice as CSV",
        data=movies[present].to_csv(index=False).encode("utf-8"),
        file_name="movies_filtered.csv",
        mime="text/csv",
        **_width_kwargs(st.download_button, stretch=False),
    )


def main() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)

    movies, sales = load_catalog()
    if movies is None or movies.empty:
        st.error(
            "Data files not found. From the repo root run `python3 scripts/generate_data.py` "
            "then `python3 scripts/data_processing.py`."
        )
        st.stop()

    if "filter_epoch" not in st.session_state:
        st.session_state.filter_epoch = 0
    epoch = st.session_state.filter_epoch

    min_date = pd.Timestamp(movies["release_date"].min()).date()
    max_date = pd.Timestamp(movies["release_date"].max()).date()
    genres_all = unique_sorted(movies["genre"])
    studios_all = unique_sorted(movies["studio"])
    budget_hi = int(max(movies["budget"].max() / 1_000_000, 1))

    st.title("🎬 Movie Industry Analytics Dashboard")
    st.markdown(
        '<p class="source-note">Most rows are published production budgets and box office from '
        "<strong>The Numbers</strong> (TidyTuesday extract). Household-name films missing from that extract "
        "(Avatar, Titanic, The Dark Knight, Endgame, and similar) are filled in from widely reported figures. "
        "IMDb scores are joined from the public IMDb 5000 extract plus those published ratings. "
        "Daily tickets are an 8-week theatrical model scaled to each film’s domestic gross.</p>",
        unsafe_allow_html=True,
    )

    st.sidebar.header("🔍 Filters")
    if st.sidebar.button("Reset filters", key="reset-filters"):
        st.session_state.filter_epoch += 1
        st.rerun()

    search = st.sidebar.text_input("Search titles", placeholder="e.g. Star Wars, Zootopia", key=f"search-{epoch}")
    date_value = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key=f"dates-{epoch}",
    )
    selected_genres = st.sidebar.multiselect(
        "Select Genres", options=genres_all, default=genres_all, key=f"genres-{epoch}"
    )
    selected_studios = st.sidebar.multiselect(
        "Studios (optional)",
        options=studios_all,
        default=[],
        key=f"studios-{epoch}",
        help="Leave empty to include every studio. Selecting none of 200+ studios by default would flood the sidebar.",
    )
    budget_range = st.sidebar.slider(
        "Budget Range (Millions)",
        min_value=0,
        max_value=budget_hi,
        value=(0, budget_hi),
        step=max(1, budget_hi // 40),
        key=f"budget-{epoch}",
    )
    st.sidebar.caption(f"{len(movies):,} titles in the catalog · {0 if sales is None else len(sales):,} modeled daily sales rows")

    date_start, date_end = normalize_date_range(date_value, min_date, max_date)
    filtered = filter_movies(
        movies,
        date_start=date_start,
        date_end=date_end,
        genres=selected_genres,
        studios=selected_studios if selected_studios else None,
        budget_min=budget_range[0] * 1_000_000,
        budget_max=budget_range[1] * 1_000_000,
        search=search,
    )
    kpis = compute_overview_metrics(filtered)
    sliced_sales = filter_sales(sales, filtered["movie_id"]) if sales is not None else None

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Movies", fmt_number(kpis["total_movies"]))
    k2.metric("Total Box Office", fmt_money(kpis["total_revenue"]))
    k3.metric("Avg IMDb Rating", fmt_rating(kpis["avg_rating"]))
    k4.metric("Profitable Movies", fmt_pct(kpis["profitable_percentage"]))
    k5.metric("Median ROI", fmt_pct(kpis["median_roi"]), help="Median is used instead of the mean because a handful of ultra-low-budget hits skew the average.")

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📊 Overview", "🎭 Genre Analysis", "🏢 Studio Performance", "📈 Trends", "🎫 Sales Data", "📋 Catalog"]
    )

    if filtered.empty:
        for tab in (tab1, tab2, tab3, tab4, tab5, tab6):
            with tab:
                st.info("No titles match the current filters. Reset filters or widen the date range.")
        return

    with tab1:
        show_overview_tab(filtered)
    with tab2:
        show_genre_analysis(filtered)
    with tab3:
        show_studio_analysis(filtered)
    with tab4:
        show_trends_analysis(filtered)
    with tab5:
        show_sales_analysis(sliced_sales, n_modeled=100)
    with tab6:
        show_catalog(filtered)


if __name__ == "__main__":
    main()
