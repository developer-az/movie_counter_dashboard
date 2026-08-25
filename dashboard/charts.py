"""
Production Plotly chart builders.

Figures are returned as objects so they can be tested without Streamlit.
Traces use WebGL (scattergl) and pre-aggregated frames so the UI stays
responsive as catalogs grow from hundreds to hundreds of thousands of rows.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from analytics.core import sample_for_chart

PALETTE = [
    "#F5C542",
    "#5B8DEF",
    "#3DDC97",
    "#F07167",
    "#C084FC",
    "#22D3EE",
    "#FB923C",
    "#F472B6",
    "#A3E635",
    "#94A3B8",
]

PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def apply_layout(fig: go.Figure, title: str, height: int = 420, y_title: str = "", x_title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color="#E8EEF6", family="IBM Plex Sans, Inter, sans-serif"),
            x=0,
            xanchor="left",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(16, 22, 31, 0.55)",
        font=dict(family="IBM Plex Sans, Inter, system-ui, sans-serif", color="#C5D0DC", size=12),
        margin=dict(l=12, r=12, t=58, b=12),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
        hoverlabel=dict(bgcolor="#1C2633", font_size=12, font_color="#E8EEF6", bordercolor="#2A3544"),
        colorway=PALETTE,
        bargap=0.28,
    )
    fig.update_xaxes(
        title_text=x_title,
        gridcolor="rgba(255,255,255,0.06)",
        zeroline=False,
        showline=False,
        automargin=True,
    )
    fig.update_yaxes(
        title_text=y_title,
        gridcolor="rgba(255,255,255,0.06)",
        zeroline=False,
        showline=False,
        automargin=True,
    )
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
        font=dict(size=14, color="#8B9BB0"),
    )
    apply_layout(fig, title, height=360)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def budget_vs_gross(movies: pd.DataFrame, max_points: int) -> tuple[go.Figure, Optional[str]]:
    if movies is None or movies.empty:
        return empty_figure("Budget vs box office"), None

    plotted, sampled, original = sample_for_chart(movies, max_points=max_points, by="genre")
    fig = px.scatter(
        plotted,
        x="budget",
        y="total_gross",
        color="genre",
        hover_name="title",
        hover_data={"budget": ":$,.0f", "total_gross": ":$,.0f", "imdb_rating": ":.1f", "genre": True},
        render_mode="webgl",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(marker=dict(size=8, opacity=0.75, line=dict(width=0)))
    apply_layout(fig, "Budget vs box office", y_title="Box office", x_title="Production budget")
    fig.update_xaxes(tickformat="$.2s")
    fig.update_yaxes(tickformat="$.2s")
    note = (
        f"Plotting {len(plotted):,} of {original:,} titles (stratified sample) to keep the GPU trace light."
        if sampled
        else None
    )
    return fig, note


def roi_distribution(movies: pd.DataFrame) -> go.Figure:
    if movies is None or movies.empty:
        return empty_figure("Return on investment")

    fig = px.histogram(movies, x="roi", nbins=min(40, max(12, len(movies) // 8)), color_discrete_sequence=[PALETTE[0]])
    median = float(movies["roi"].median())
    fig.add_vline(
        x=median,
        line_dash="dash",
        line_color="#5B8DEF",
        annotation_text=f"Median {median:.0f}%",
        annotation_position="top right",
        annotation_font_color="#8B9BB0",
    )
    fig.update_traces(marker_line_width=0, opacity=0.9)
    apply_layout(fig, "Return on investment", y_title="Titles", x_title="ROI %")
    return fig


def genre_revenue_treemap(stats: pd.DataFrame) -> go.Figure:
    if stats is None or stats.empty:
        return empty_figure("Box office share by genre")

    fig = px.treemap(
        stats,
        path=["genre"],
        values="total_gross",
        color="avg_rating",
        color_continuous_scale=["#1C2633", "#5B8DEF", "#F5C542"],
        hover_data={"movie_count": True, "avg_roi": ":.1f", "avg_rating": ":.2f"},
    )
    fig.update_traces(textinfo="label+percent entry", hovertemplate="%{label}<br>Box office: %{value:$,.0f}<extra></extra>")
    apply_layout(fig, "Box office share by genre", height=460)
    fig.update_layout(coloraxis_colorbar=dict(title="Avg IMDb", thickness=12))
    return fig


def genre_bar(stats: pd.DataFrame, metric: str, title: str, y_title: str, money: bool = False) -> go.Figure:
    if stats is None or stats.empty or metric not in stats.columns:
        return empty_figure(title)

    ordered = stats.sort_values(metric, ascending=True)
    fig = px.bar(ordered, x=metric, y="genre", orientation="h", color_discrete_sequence=[PALETTE[1]])
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:,.1f}<extra></extra>")
    apply_layout(fig, title, y_title="", x_title=y_title, height=420)
    if money:
        fig.update_xaxes(tickformat="$.2s")
    return fig


def studio_revenue_bar(stats: pd.DataFrame, limit: int = 15) -> go.Figure:
    if stats is None or stats.empty:
        return empty_figure("Top studios by box office")

    top = stats.nlargest(limit, "total_gross").sort_values("total_gross", ascending=True)
    fig = px.bar(top, x="total_gross", y="studio", orientation="h", color_discrete_sequence=[PALETTE[0]])
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:$,.0f}<extra></extra>")
    apply_layout(fig, f"Top {min(limit, len(top))} studios by box office", x_title="Box office")
    fig.update_xaxes(tickformat="$.2s")
    return fig


def studio_volume_vs_yield(stats: pd.DataFrame) -> go.Figure:
    if stats is None or stats.empty:
        return empty_figure("Volume vs average yield")

    fig = px.scatter(
        stats,
        x="movie_count",
        y="avg_gross",
        size="total_gross",
        color="avg_rating",
        hover_name="studio",
        color_continuous_scale=["#5B8DEF", "#F5C542"],
        render_mode="webgl",
    )
    fig.update_traces(marker=dict(opacity=0.85, line=dict(width=0)))
    apply_layout(fig, "Volume vs average yield", x_title="Titles released", y_title="Avg box office")
    fig.update_yaxes(tickformat="$.2s")
    fig.update_layout(coloraxis_colorbar=dict(title="Avg IMDb", thickness=12))
    return fig


def yearly_line(frame: pd.DataFrame, y: str, title: str, y_title: str, money: bool = False) -> go.Figure:
    if frame is None or frame.empty:
        return empty_figure(title)

    fig = px.line(frame, x="release_year", y=y, markers=True, color_discrete_sequence=[PALETTE[1]])
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
    apply_layout(fig, title, x_title="Release year", y_title=y_title)
    if money:
        fig.update_yaxes(tickformat="$.2s")
    return fig


def rating_over_time(movies: pd.DataFrame, max_points: int) -> tuple[go.Figure, Optional[str]]:
    if movies is None or movies.empty:
        return empty_figure("Ratings over time"), None

    plotted, sampled, original = sample_for_chart(movies, max_points=max_points, by="genre")
    fig = px.scatter(
        plotted,
        x="release_year",
        y="imdb_rating",
        size="budget",
        color="genre",
        hover_name="title",
        render_mode="webgl",
        color_discrete_sequence=PALETTE,
        size_max=24,
    )
    apply_layout(fig, "Audience score vs release year", x_title="Release year", y_title="IMDb")
    note = f"Plotting {len(plotted):,} of {original:,} titles." if sampled else None
    return fig, note


def sales_line(frame: pd.DataFrame, y: str, title: str, y_title: str, grain: str, money: bool = False) -> go.Figure:
    if frame is None or frame.empty:
        return empty_figure(title)

    x_col = "date" if "date" in frame.columns else frame.columns[0]
    fig = px.line(frame, x=x_col, y=y, color_discrete_sequence=[PALETTE[0] if money else PALETTE[2]])
    fig.update_traces(line=dict(width=2), hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f}<extra></extra>")
    apply_layout(fig, f"{title} · {grain}", x_title="", y_title=y_title)
    if money:
        fig.update_yaxes(tickformat="$.2s")
    return fig


def weekend_bar(frame: pd.DataFrame, y: str, title: str, y_title: str) -> go.Figure:
    if frame is None or frame.empty:
        return empty_figure(title)

    fig = px.bar(frame, x="day_type", y=y, color="day_type", color_discrete_sequence=[PALETTE[1], PALETTE[0]])
    fig.update_traces(marker_line_width=0)
    apply_layout(fig, title, x_title="", y_title=y_title)
    fig.update_layout(showlegend=False)
    return fig


def top_titles_bar(frame: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    if frame is None or frame.empty:
        return empty_figure(title)

    ordered = frame.sort_values(x, ascending=True)
    fig = px.bar(ordered, x=x, y=y, orientation="h", color_discrete_sequence=[PALETTE[5]])
    fig.update_traces(marker_line_width=0)
    apply_layout(fig, title, x_title="", y_title="")
    return fig


def roi_by_genre_box(movies: pd.DataFrame) -> go.Figure:
    if movies is None or movies.empty:
        return empty_figure("ROI spread by genre")

    order = movies.groupby("genre", observed=True)["roi"].median().sort_values(ascending=False).index.tolist()
    fig = px.box(
        movies,
        x="genre",
        y="roi",
        color="genre",
        category_orders={"genre": order},
        color_discrete_sequence=PALETTE,
        points=False,
    )
    apply_layout(fig, "ROI spread by genre", x_title="", y_title="ROI %", height=420)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(tickangle=-25)
    return fig


def format_sample_caption(sampled: bool, shown: int, original: int, extra: str = "") -> Optional[str]:
    if not sampled:
        return extra or None
    base = f"Showing {shown:,} of {original:,} rows to keep this view interactive."
    return f"{base} {extra}".strip() if extra else base
