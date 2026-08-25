"""
Core Analytics Functions

Shared analytics functions that can be used by both dashboard and terminal interfaces.
Provides consistent data analysis capabilities across different output formats.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "processed"

CATEGORICAL_COLUMNS = {
    "genre",
    "studio",
    "rating",
    "budget_category",
    "performance",
    "day_of_week",
    "movie_title",
}

# Chart budgets: keep traces GPU-friendly even when the source table is huge.
MAX_SCATTER_POINTS = 4_000
MAX_SCATTER_POINTS_FAST = 2_000
MAX_LINE_POINTS = 1_500
LARGE_FRAME_ROWS = 250_000

DateLike = Union[str, datetime, pd.Timestamp]


def resolve_data_path(data_path: Union[str, Path] = "data/processed") -> Path:
    """
    Resolve the processed-data directory regardless of the current working directory.

    Streamlit, tests, and the CLI each start from different folders. Prefer an
    explicit path that already contains movies_processed.csv, then search common
    project-relative locations.
    """
    requested = Path(data_path)
    marker = "movies_processed.csv"

    candidates = [requested]
    if not requested.is_absolute():
        candidates.extend(
            [
                Path.cwd() / requested,
                PROJECT_ROOT / requested,
                PROJECT_ROOT / "data" / "processed",
                Path.cwd() / "data" / "processed",
                Path.cwd().parent / "data" / "processed",
            ]
        )

    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if (candidate / marker).exists():
            return candidate.resolve()

    return requested


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce memory footprint without changing analytics results.

    Categorical encoding of repeated strings and downcasting of integer id/count
    columns keeps large extracts in RAM for interactive filtering.
    """
    if df is None or df.empty:
        return df

    out = df.copy()
    for column in out.columns:
        series = out[column]
        if column in CATEGORICAL_COLUMNS and not isinstance(series.dtype, pd.CategoricalDtype):
            out[column] = series.astype("category")
        elif pd.api.types.is_bool_dtype(series) or str(series.dtype) == "boolean":
            continue
        elif pd.api.types.is_integer_dtype(series):
            out[column] = pd.to_numeric(series, downcast="integer")
        elif column == "imdb_rating" and pd.api.types.is_float_dtype(series):
            out[column] = series.astype("float32")
    return out


def frame_memory_bytes(df: Optional[pd.DataFrame]) -> int:
    """Return deep memory usage for a frame, or 0 when missing."""
    if df is None or df.empty:
        return 0
    return int(df.memory_usage(deep=True).sum())


def normalize_date_range(
    value: Any,
    fallback_min: DateLike,
    fallback_max: DateLike,
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Coerce Streamlit date_input output (1 or 2 values) into a closed timestamp range."""
    start = pd.Timestamp(fallback_min)
    end = pd.Timestamp(fallback_max)

    if value is None:
        return start.normalize(), end.normalize()

    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and value[0] is not None and value[1] is not None:
            start, end = pd.Timestamp(value[0]), pd.Timestamp(value[1])
        elif len(value) == 1 and value[0] is not None:
            start = end = pd.Timestamp(value[0])
    else:
        start = end = pd.Timestamp(value)

    if start > end:
        start, end = end, start
    return start.normalize(), end.normalize()


def previous_period_bounds(
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return the equally long window immediately before ``start`` (for KPI deltas)."""
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    span_days = max((end.normalize() - start.normalize()).days, 0)
    prev_end = start.normalize() - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=span_days)
    return prev_start, prev_end


def filter_movies(
    movies: pd.DataFrame,
    *,
    date_start: Optional[DateLike] = None,
    date_end: Optional[DateLike] = None,
    genres: Optional[Sequence[str]] = None,
    studios: Optional[Sequence[str]] = None,
    ratings: Optional[Sequence[str]] = None,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    imdb_min: Optional[float] = None,
    imdb_max: Optional[float] = None,
    search: Optional[str] = None,
) -> pd.DataFrame:
    """
    Vectorized filter over the movies frame.

    Empty sequences mean "no extra restriction" for the corresponding dimension,
    which is the production-friendly default when a catalog has hundreds of studios.
    """
    if movies is None or movies.empty:
        return movies if movies is not None else pd.DataFrame()

    mask = pd.Series(True, index=movies.index)

    if date_start is not None:
        mask &= movies["release_date"] >= pd.Timestamp(date_start)
    if date_end is not None:
        mask &= movies["release_date"] <= (
            pd.Timestamp(date_end) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
        )
    # None = no restriction; empty sequence = match nothing (cleared multiselect).
    if genres is not None:
        mask &= movies["genre"].isin(list(genres))
    if studios is not None:
        mask &= movies["studio"].isin(list(studios))
    if ratings is not None:
        mask &= movies["rating"].isin(list(ratings))
    if budget_min is not None:
        mask &= movies["budget"] >= budget_min
    if budget_max is not None:
        mask &= movies["budget"] <= budget_max
    if imdb_min is not None:
        mask &= movies["imdb_rating"] >= imdb_min
    if imdb_max is not None:
        mask &= movies["imdb_rating"] <= imdb_max
    if search:
        needle = str(search).strip()
        if needle:
            mask &= movies["title"].astype(str).str.contains(
                needle, case=False, na=False, regex=False
            )

    return movies.loc[mask]


def filter_sales(sales: pd.DataFrame, movie_ids: Optional[Iterable[Any]] = None) -> pd.DataFrame:
    """Restrict sales rows to the currently selected titles."""
    if sales is None or sales.empty or movie_ids is None:
        return sales if sales is not None else pd.DataFrame()
    ids = pd.unique(pd.Index(list(movie_ids)))
    if len(ids) == 0:
        return sales.iloc[0:0]
    return sales.loc[sales["movie_id"].isin(ids)]


def compute_overview_metrics(movies: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """Empty-safe KPI payload used by the dashboard, CLI, and tests."""
    empty = {
        "total_movies": 0,
        "total_revenue": 0.0,
        "avg_rating": None,
        "profitable_movies": 0,
        "profitable_percentage": 0.0,
        "avg_roi": None,
        "median_roi": None,
        "total_budget": 0.0,
        "total_profit": 0.0,
        "genres_count": 0,
        "studios_count": 0,
        "date_range": {"start": None, "end": None},
    }
    if movies is None or movies.empty:
        return empty

    profitable = movies["profit"] > 0
    return {
        "total_movies": int(len(movies)),
        "total_revenue": float(movies["total_gross"].sum()),
        "avg_rating": float(movies["imdb_rating"].mean()),
        "profitable_movies": int(profitable.sum()),
        "profitable_percentage": float(profitable.mean() * 100),
        "avg_roi": float(movies["roi"].mean()),
        "median_roi": float(movies["roi"].median()),
        "total_budget": float(movies["budget"].sum()),
        "total_profit": float(movies["profit"].sum()),
        "genres_count": int(movies["genre"].nunique()),
        "studios_count": int(movies["studio"].nunique()),
        "date_range": {
            "start": movies["release_date"].min(),
            "end": movies["release_date"].max(),
        },
    }


def compute_genre_stats(movies: pd.DataFrame) -> pd.DataFrame:
    """Live genre aggregates from the filtered catalog (not the static CSV)."""
    columns = [
        "genre",
        "movie_count",
        "avg_budget",
        "median_budget",
        "avg_gross",
        "median_gross",
        "total_gross",
        "avg_rating",
        "avg_profit",
        "median_profit",
        "avg_roi",
        "profitable_pct",
    ]
    if movies is None or movies.empty:
        return pd.DataFrame(columns=columns)

    stats = (
        movies.groupby("genre", observed=True)
        .agg(
            movie_count=("movie_id", "count"),
            avg_budget=("budget", "mean"),
            median_budget=("budget", "median"),
            avg_gross=("total_gross", "mean"),
            median_gross=("total_gross", "median"),
            total_gross=("total_gross", "sum"),
            avg_rating=("imdb_rating", "mean"),
            avg_profit=("profit", "mean"),
            median_profit=("profit", "median"),
            avg_roi=("roi", "mean"),
            profitable_pct=("profit", lambda s: float((s > 0).mean() * 100)),
        )
        .reset_index()
        .sort_values("total_gross", ascending=False)
    )
    return stats.round(2)


def compute_studio_stats(movies: pd.DataFrame) -> pd.DataFrame:
    """Live studio aggregates from the filtered catalog."""
    columns = [
        "studio",
        "movie_count",
        "avg_budget",
        "total_budget",
        "avg_gross",
        "total_gross",
        "avg_rating",
        "avg_roi",
        "profitable_pct",
    ]
    if movies is None or movies.empty:
        return pd.DataFrame(columns=columns)

    stats = (
        movies.groupby("studio", observed=True)
        .agg(
            movie_count=("movie_id", "count"),
            avg_budget=("budget", "mean"),
            total_budget=("budget", "sum"),
            avg_gross=("total_gross", "mean"),
            total_gross=("total_gross", "sum"),
            avg_rating=("imdb_rating", "mean"),
            avg_roi=("roi", "mean"),
            profitable_pct=("profit", lambda s: float((s > 0).mean() * 100)),
        )
        .reset_index()
        .sort_values("total_gross", ascending=False)
    )
    return stats.round(2)


def sample_for_chart(
    df: pd.DataFrame,
    max_points: int = MAX_SCATTER_POINTS,
    by: Optional[str] = None,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, bool, int]:
    """
    Downsample a frame for scatter/detail charts.

    Returns (frame, was_sampled, original_len). Uses stride sampling above
    LARGE_FRAME_ROWS so we never shuffle a million-row table just to draw dots.
    """
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame(), False, 0

    n = len(df)
    cap = max(int(max_points), 1)
    if n <= cap:
        return df, False, n

    if n > LARGE_FRAME_ROWS or by is None or by not in df.columns:
        step = max(1, n // cap)
        sampled = df.iloc[::step].head(cap)
        return sampled, True, n

    frac = min(1.0, cap / n)
    sampled = df.groupby(by, observed=True, group_keys=False).sample(
        frac=frac, random_state=random_state
    )
    if len(sampled) > cap:
        sampled = sampled.sample(n=cap, random_state=random_state)
    return sampled, True, n


def auto_resample_timeseries(
    df: pd.DataFrame,
    date_col: str,
    value_cols: Sequence[str],
    max_points: int = MAX_LINE_POINTS,
) -> Tuple[pd.DataFrame, str]:
    """
    Aggregate a time series to day/week/month/quarter so line charts stay readable.

    Returns (aggregated_frame, grain_label).
    """
    if df is None or df.empty or date_col not in df.columns:
        return pd.DataFrame(columns=[date_col, *value_cols]), "day"

    working = df[[date_col, *list(value_cols)]].copy()
    working[date_col] = pd.to_datetime(working[date_col])
    daily = working.groupby(working[date_col].dt.normalize(), observed=True)[list(value_cols)].sum()
    daily.index.name = date_col
    n = len(daily)
    if n <= max_points:
        return daily.reset_index(), "day"

    span_days = max((daily.index.max() - daily.index.min()).days, 1)
    if span_days / 7 <= max_points:
        freq, grain = "W", "week"
    elif span_days / 30 <= max_points:
        freq, grain = "MS", "month"
    else:
        freq, grain = "QS", "quarter"

    resampled = daily.resample(freq).sum().reset_index()
    return resampled, grain


def unique_sorted(series: pd.Series) -> List[Any]:
    """Stable unique values for filter widgets, including categoricals."""
    if series is None or series.empty:
        return []
    values = pd.Series(series.dropna().unique())
    try:
        return sorted(values.tolist())
    except TypeError:
        return values.tolist()


class MovieAnalytics:
    """
    Core analytics class for movie industry data analysis.
    
    Provides methods for loading data, calculating metrics, and generating insights
    that can be used by different interfaces (dashboard, terminal, API).
    """
    
    def __init__(self, data_path: str = "data/processed"):
        """
        Initialize MovieAnalytics with data path.
        
        Args:
            data_path: Path to processed data files
        """
        self.data_path = resolve_data_path(data_path)
        self._movies = None
        self._sales = None
        self._genre_stats = None
        self._studio_stats = None
        self._monthly_sales = None
    
    def load_data(self) -> bool:
        """
        Load all datasets from processed files.
        
        Returns:
            bool: True if all data loaded successfully, False otherwise
        """
        try:
            self.data_path = resolve_data_path(self.data_path)
            self._movies = optimize_dtypes(
                pd.read_csv(self.data_path / "movies_processed.csv", parse_dates=["release_date"])
            )
            self._sales = optimize_dtypes(
                pd.read_csv(self.data_path / "sales_processed.csv", parse_dates=["date"])
            )
            if "is_weekend" in self._sales.columns and self._sales["is_weekend"].dtype == object:
                self._sales["is_weekend"] = self._sales["is_weekend"].map(
                    {"True": True, "False": False, True: True, False: False}
                ).astype("boolean")
            self._genre_stats = pd.read_csv(self.data_path / "genre_stats.csv")
            self._studio_stats = pd.read_csv(self.data_path / "studio_stats.csv")
            self._monthly_sales = pd.read_csv(self.data_path / "monthly_sales.csv")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def get_overview_metrics(self) -> Dict[str, Any]:
        """
        Get key overview metrics for the dataset.
        
        Returns:
            Dict containing overview metrics
        """
        if self._movies is None:
            return {}
        return compute_overview_metrics(self._movies)
    
    def get_genre_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive genre analysis.
        
        Returns:
            Dict containing genre analysis data
        """
        if self._movies is None or self._genre_stats is None:
            return {}
        
        # Genre distribution
        genre_counts = self._movies['genre'].value_counts()
        
        # Top performing genres by different metrics - handle empty dataframe
        if len(self._genre_stats) == 0:
            return {'genre_distribution': genre_counts.to_dict()}
        
        # Find columns that exist
        revenue_col = 'total_gross' if 'total_gross' in self._genre_stats.columns else 'total_revenue'
        rating_col = 'avg_rating' if 'avg_rating' in self._genre_stats.columns else 'rating'  
        profit_col = 'avg_profit' if 'avg_profit' in self._genre_stats.columns else 'profit'
        
        top_revenue_genre = self._genre_stats.loc[self._genre_stats[revenue_col].idxmax()]
        top_rating_genre = self._genre_stats.loc[self._genre_stats[rating_col].idxmax()]
        top_profit_genre = self._genre_stats.loc[self._genre_stats[profit_col].idxmax()]
        
        return {
            'genre_distribution': genre_counts.to_dict(),
            'top_revenue_genre': {
                'name': top_revenue_genre['genre'],
                'revenue': top_revenue_genre[revenue_col]
            },
            'top_rating_genre': {
                'name': top_rating_genre['genre'],
                'rating': top_rating_genre[rating_col]
            },
            'top_profit_genre': {
                'name': top_profit_genre['genre'],
                'profit': top_profit_genre[profit_col]
            },
            'genre_stats': self._genre_stats.to_dict('records')
        }
    
    def get_studio_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive studio analysis.
        
        Returns:
            Dict containing studio analysis data
        """
        if self._movies is None or self._studio_stats is None:
            return {}
        
        # Top performing studios
        revenue_col = 'total_gross' if 'total_gross' in self._studio_stats.columns else 'total_revenue'
        avg_revenue_col = 'avg_gross' if 'avg_gross' in self._studio_stats.columns else 'avg_revenue'
        
        top_revenue_studio = self._studio_stats.loc[self._studio_stats[revenue_col].idxmax()]
        most_active_studio = self._studio_stats.loc[self._studio_stats['movie_count'].idxmax()]
        top_avg_revenue_studio = self._studio_stats.loc[self._studio_stats[avg_revenue_col].idxmax()]
        
        return {
            'top_revenue_studio': {
                'name': top_revenue_studio['studio'],
                'revenue': top_revenue_studio[revenue_col]
            },
            'most_active_studio': {
                'name': most_active_studio['studio'],
                'movie_count': most_active_studio['movie_count']
            },
            'top_avg_revenue_studio': {
                'name': top_avg_revenue_studio['studio'],
                'avg_revenue': top_avg_revenue_studio[avg_revenue_col]
            },
            'studio_stats': self._studio_stats.to_dict('records')
        }
    
    def get_temporal_trends(self) -> Dict[str, Any]:
        """
        Get temporal analysis of movie trends.
        
        Returns:
            Dict containing temporal analysis data
        """
        if self._movies is None:
            return {}
        
        # Movies by release year
        movies_by_year = self._movies.groupby(self._movies['release_date'].dt.year).size()
        
        # Revenue trends by year
        revenue_by_year = self._movies.groupby(self._movies['release_date'].dt.year)['total_gross'].mean()
        
        # Rating trends by year
        rating_by_year = self._movies.groupby(self._movies['release_date'].dt.year)['imdb_rating'].mean()
        
        return {
            'movies_by_year': movies_by_year.to_dict(),
            'revenue_trends': revenue_by_year.to_dict(),
            'rating_trends': rating_by_year.to_dict(),
            'total_years': len(movies_by_year)
        }
    
    def get_sales_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive sales analysis.
        
        Returns:
            Dict containing sales analysis data
        """
        if self._sales is None:
            return {}
        
        # Total sales metrics
        total_tickets = self._sales['tickets_sold'].sum()
        total_sales_revenue = self._sales['revenue'].sum()
        avg_daily_tickets = self._sales['tickets_sold'].mean()
        
        # Top movies by ticket sales
        top_movies_tickets = self._sales.groupby('movie_title')['tickets_sold'].sum().sort_values(ascending=False).head(10)
        
        # Weekend vs weekday analysis
        self._sales['day_of_week'] = self._sales['date'].dt.dayofweek
        weekend_sales = self._sales[self._sales['day_of_week'].isin([5, 6])]['tickets_sold'].mean()
        weekday_sales = self._sales[~self._sales['day_of_week'].isin([5, 6])]['tickets_sold'].mean()
        
        return {
            'total_tickets_sold': total_tickets,
            'total_sales_revenue': total_sales_revenue,
            'avg_daily_tickets': avg_daily_tickets,
            'top_movies_by_tickets': top_movies_tickets.to_dict(),
            'weekend_vs_weekday': {
                'weekend_avg': weekend_sales,
                'weekday_avg': weekday_sales,
                'weekend_boost': (weekend_sales / weekday_sales - 1) * 100 if weekday_sales > 0 else 0
            },
            'sales_date_range': {
                'start': self._sales['date'].min(),
                'end': self._sales['date'].max()
            }
        }
    
    def get_top_performers(self, metric: str = 'revenue', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing movies by specified metric.
        
        Args:
            metric: Metric to sort by ('revenue', 'profit', 'rating', 'roi')
            limit: Number of top performers to return
            
        Returns:
            List of movie dictionaries
        """
        if self._movies is None:
            return []
        
        metric_column_map = {
            'revenue': 'total_gross',
            'profit': 'profit',
            'rating': 'imdb_rating',
            'roi': 'roi'
        }
        
        if metric not in metric_column_map:
            return []
        
        column = metric_column_map[metric]
        top_movies = self._movies.nlargest(limit, column)
        
        return top_movies[['title', 'genre', 'studio', 'release_date', 'budget', 'total_gross', 'profit', 'imdb_rating', 'roi']].to_dict('records')
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive analytics report.
        
        Returns:
            Dict containing all analytics data
        """
        return {
            'overview': self.get_overview_metrics(),
            'genre_analysis': self.get_genre_analysis(),
            'studio_analysis': self.get_studio_analysis(),
            'temporal_trends': self.get_temporal_trends(),
            'sales_analysis': self.get_sales_analysis(),
            'top_performers': {
                'by_revenue': self.get_top_performers('revenue', 5),
                'by_profit': self.get_top_performers('profit', 5),
                'by_rating': self.get_top_performers('rating', 5),
                'by_roi': self.get_top_performers('roi', 5)
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def export_report(self, format_type: str = 'json', output_path: str = None) -> str:
        """
        Export comprehensive report to specified format.
        
        Args:
            format_type: Export format ('json', 'csv')
            output_path: Output file path (optional)
            
        Returns:
            String representation of the report or file path
        """
        report = self.get_comprehensive_report()
        
        if format_type.lower() == 'json':
            if output_path:
                with open(output_path, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                return output_path
            else:
                return json.dumps(report, indent=2, default=str)
        
        elif format_type.lower() == 'csv':
            # For CSV, export key metrics as a flat structure
            overview = report['overview']
            csv_data = {
                'metric': ['total_movies', 'total_revenue', 'avg_rating', 'profitable_percentage', 'avg_roi'],
                'value': [
                    overview['total_movies'],
                    overview['total_revenue'],
                    overview['avg_rating'],
                    overview['profitable_percentage'],
                    overview['avg_roi']
                ]
            }
            df = pd.DataFrame(csv_data)
            
            if output_path:
                df.to_csv(output_path, index=False)
                return output_path
            else:
                return df.to_csv(index=False)
        
        return json.dumps(report, indent=2, default=str)
    
    @property
    def movies(self) -> Optional[pd.DataFrame]:
        """Get movies dataframe."""
        return self._movies
    
    @property
    def sales(self) -> Optional[pd.DataFrame]:
        """Get sales dataframe."""
        return self._sales
    
    @property
    def is_data_loaded(self) -> bool:
        """Check if data is loaded."""
        return all([
            self._movies is not None,
            self._sales is not None,
            self._genre_stats is not None,
            self._studio_stats is not None,
            self._monthly_sales is not None
        ])