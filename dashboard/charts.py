"""
Plotly chart builders for the movie dashboard.

Keep the original chart set (scatter, histogram, pie, bars, lines) and add
only overlays that make the same figure more useful: break-even, 0% ROI,
and currency axes. Light styling so Streamlit's default theme is not fighting
a second dark skin.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from analytics.core import sample_for_chart

PALETTE = [
    "#2563EB",
    "#DC2626",
    "#059669",
    "#D97706",
    "#7C3AED",
    "#0891B2",
    "#DB2777",
    "#4F46E5",
    "#65A30D",
    "#EA580C",
]

PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def apply_layout(fig: go.Figure, title: str, height: int = 440, y_title: str = "", x_title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#0F172A"), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Source Sans 3, Segoe UI, sans-serif", color="#334155", size=12),
        margin=dict(l=8, r=8, t=56, b=8),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="white", font_size=12, font_color="#0F172A"),
        colorway=PALETTE,
        bargap=0.25,
    )
    fig.update_xaxes(title_text=x_title, gridcolor="#E2E8F0", zeroline=False, automargin=True)
    fig.update_yaxes(title_text=y_title, gridcolor="#E2E8F0", zeroline=False, automargin=True)
    return fig


def empty_figure(title: str, message: str = "No titles match the current filters.") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#64748B"),
    )
    apply_layout(fig, title, height=360)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def budget_vs_gross(movies: pd.DataFrame, max_points: int) -> tuple[go.Figure, Optional[str]]:
    if movies is None or movies.empty:
        return empty_figure("Budget vs Total Gross Revenue"), None

    plotted, sampled, original = sample_for_chart(movies, max_points=max_points, by="genre")
    fig = px.scatter(
        plotted,
        x="budget",
        y="total_gross",
        color="genre",
        hover_name="title",
        hover_data={
            "studio": True,
            "budget": ":$,.0f",
            "total_gross": ":$,.0f",
            "imdb_rating": ":.1f",
            "genre": True,
        },
        render_mode="webgl",
        color_discrete_sequence=PALETTE,
        log_x=True,
        log_y=True,
    )
    fig.update_traces(marker=dict(size=9, opacity=0.7, line=dict(width=0.4, color="white")))

    finite = plotted[(plotted["budget"] > 0) & (plotted["total_gross"] > 0)]
    if not finite.empty:
        lo = float(min(finite["budget"].min(), finite["total_gross"].min()))
        hi = float(max(finite["budget"].max(), finite["total_gross"].max()))
        fig.add_trace(
            go.Scatter(
                x=[lo, hi],
                y=[lo, hi],
                mode="lines",
                name="Break-even (gross = budget)",
                line=dict(color="#64748B", width=1.5, dash="dash"),
                hovertemplate="Break-even<extra></extra>",
            )
        )

    apply_layout(fig, "Budget vs Total Gross Revenue", y_title="Worldwide box office", x_title="Production budget")
    fig.update_xaxes(tickformat="$.2s")
    fig.update_yaxes(tickformat="$.2s")
    note = (
        f"Showing {len(plotted):,} of {original:,} titles. Dashed line is break-even; points above it recouped their budget."
        if sampled
        else "Log scale so smaller films remain visible. Dashed line is break-even (box office = budget)."
    )
    return fig, note


def roi_distribution(movies: pd.DataFrame) -> go.Figure:
    if movies is None or movies.empty:
        return empty_figure("Return on Investment Distribution")

    series = movies["roi"].dropna()
    if series.empty:
        return empty_figure("Return on Investment Distribution")

    low, high = series.quantile(0.05), series.quantile(0.95)
    clipped = movies[(movies["roi"] >= low) & (movies["roi"] <= high)]
    fig = px.histogram(clipped, x="roi", nbins=36, color_discrete_sequence=[PALETTE[0]])
    median = float(series.median())
    fig.add_vline(x=0, line_dash="dot", line_color="#DC2626", annotation_text="Break-even 0%", annotation_font_color="#DC2626")
    fig.add_vline(
        x=median,
        line_dash="dash",
        line_color="#059669",
        annotation_text=f"Median {median:.0f}%",
        annotation_font_color="#059669",
    )
    fig.update_traces(marker_line_width=0)
    apply_layout(fig, "Return on Investment Distribution", y_title="Number of movies", x_title="ROI %")
    return fig


def genre_pie(movies: pd.DataFrame) -> go.Figure:
    if movies is None or movies.empty:
        return empty_figure("Movie Distribution by Genre")
    counts = movies["genre"].value_counts().reset_index()
    counts.columns = ["genre", "count"]
    fig = px.pie(counts, names="genre", values="count", color_discrete_sequence=PALETTE, hole=0)
    fig.update_traces(textinfo="percent+label", hovertemplate="%{label}: %{value} movies (%{percent})<extra></extra>")
    apply_layout(fig, "Movie Distribution by Genre", height=440)
    fig.update_layout(legend=dict(orientation="v", y=0.5, x=1.02, yanchor="middle"))
    return fig


def genre_avg_revenue_bar(stats: pd.DataFrame) -> go.Figure:
    if stats is None or stats.empty:
        return empty_figure("Average Revenue by Genre")
    ordered = stats.sort_values("avg_gross", ascending=True)
    fig = px.bar(ordered, x="avg_gross", y="genre", orientation="h", color_discrete_sequence=[PALETTE[1]])
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>Avg box office: %{x:$,.0f}<extra></extra>")
    apply_layout(fig, "Average Revenue by Genre", x_title="Average worldwide box office")
    fig.update_xaxes(tickformat="$.2s")
    return fig


def studio_revenue_bar(stats: pd.DataFrame, limit: int = 15) -> go.Figure:
    if stats is None or stats.empty:
        return empty_figure("Top 15 Studios by Total Revenue")
    top = stats.nlargest(limit, "total_gross").sort_values("total_gross", ascending=True)
    fig = px.bar(top, x="total_gross", y="studio", orientation="h", color_discrete_sequence=[PALETTE[0]])
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:$,.0f}<extra></extra>")
    apply_layout(fig, f"Top {len(top)} Studios by Total Revenue", x_title="Worldwide box office")
    fig.update_xaxes(tickformat="$.2s")
    fig.update_yaxes(categoryorder="array", categoryarray=list(top["studio"]))
    return fig


def studio_volume_vs_yield(stats: pd.DataFrame) -> go.Figure:
    if stats is None or stats.empty:
        return empty_figure("Studio Performance: Movies Count vs Average Revenue")
    fig = px.scatter(
        stats,
        x="movie_count",
        y="avg_gross",
        size="total_gross",
        hover_name="studio",
        hover_data={"movie_count": True, "avg_gross": ":$,.0f", "total_gross": ":$,.0f"},
        color_discrete_sequence=[PALETTE[2]],
        size_max=48,
    )
    fig.update_traces(marker=dict(opacity=0.75, line=dict(width=0.5, color="white")))
    apply_layout(
        fig,
        "Studio Performance: Movies Count vs Average Revenue",
        x_title="Number of movies",
        y_title="Average box office",
    )
    fig.update_yaxes(tickformat="$.2s")
    return fig


def yearly_line(frame: pd.DataFrame, y: str, title: str, y_title: str, money: bool = False) -> go.Figure:
    if frame is None or frame.empty:
        return empty_figure(title)
    fig = px.line(frame, x="release_year", y=y, markers=True, color_discrete_sequence=[PALETTE[0]])
    fig.update_traces(line=dict(width=2.4), marker=dict(size=7))
    apply_layout(fig, title, x_title="Release year", y_title=y_title)
    if money:
        fig.update_yaxes(tickformat="$.2s")
    return fig


def rating_over_time(movies: pd.DataFrame, max_points: int) -> tuple[go.Figure, Optional[str]]:
    rated = movies.dropna(subset=["imdb_rating"]) if movies is not None else movies
    if rated is None or rated.empty:
        return empty_figure("Movie Ratings vs Release Year (Size = Budget)"), None
    plotted, sampled, original = sample_for_chart(rated, max_points=max_points, by="genre")
    fig = px.scatter(
        plotted,
        x="release_year",
        y="imdb_rating",
        size="budget",
        color="genre",
        hover_name="title",
        render_mode="webgl",
        color_discrete_sequence=PALETTE,
        size_max=28,
    )
    apply_layout(fig, "Movie Ratings vs Release Year (Size = Budget)", x_title="Release year", y_title="IMDb rating")
    note = f"Showing {len(plotted):,} of {original:,} titles with an IMDb score." if sampled else None
    return fig, note


def sales_line(frame: pd.DataFrame, y: str, title: str, y_title: str, grain: str, money: bool = False) -> go.Figure:
    if frame is None or frame.empty:
        return empty_figure(title)
    x_col = "date" if "date" in frame.columns else frame.columns[0]
    fig = px.line(frame, x=x_col, y=y, color_discrete_sequence=[PALETTE[0]])
    fig.update_traces(line=dict(width=2), hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f}<extra></extra>")
    grain_note = "" if grain == "day" else f" ({grain}ly)"
    apply_layout(fig, f"{title}{grain_note}", y_title=y_title)
    if money:
        fig.update_yaxes(tickformat="$.2s")
        fig.update_traces(hovertemplate="%{x|%Y-%m-%d}<br>%{y:$,.0f}<extra></extra>")
    return fig


def weekend_bar(frame: pd.DataFrame, y: str, title: str, y_title: str, money: bool = False) -> go.Figure:
    if frame is None or frame.empty:
        return empty_figure(title)
    order = ["Weekday", "Weekend"]
    fig = px.bar(
        frame,
        x="day_type",
        y=y,
        color="day_type",
        category_orders={"day_type": order},
        color_discrete_sequence=[PALETTE[0], PALETTE[1]],
    )
    fig.update_traces(marker_line_width=0)
    apply_layout(fig, title, x_title="", y_title=y_title)
    fig.update_layout(showlegend=False)
    if money:
        fig.update_yaxes(tickformat="$.2s")
    return fig


def top_titles_bar(frame: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    if frame is None or frame.empty:
        return empty_figure(title)
    ordered = frame.sort_values(x, ascending=True)
    fig = px.bar(ordered, x=x, y=y, orientation="h", color_discrete_sequence=[PALETTE[5]])
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>")
    apply_layout(fig, title, x_title="Tickets sold")
    fig.update_yaxes(categoryorder="array", categoryarray=list(ordered[y]))
    return fig


def roi_by_genre_box(movies: pd.DataFrame) -> go.Figure:
    if movies is None or movies.empty:
        return empty_figure("ROI spread by genre")
    order = movies.groupby("genre", observed=True)["roi"].median().sort_values(ascending=True).index.tolist()
    fig = px.box(
        movies,
        x="roi",
        y="genre",
        color="genre",
        category_orders={"genre": order},
        color_discrete_sequence=PALETTE,
        points=False,
        orientation="h",
    )
    fig.add_vline(x=0, line_dash="dot", line_color="#DC2626")
    apply_layout(fig, "ROI spread by genre", x_title="ROI %", height=420)
    fig.update_layout(showlegend=False)
    return fig
