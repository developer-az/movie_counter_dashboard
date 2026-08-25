"""
Data Processing Pipeline

This script processes raw movie data and creates clean, analysis-ready datasets.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def load_raw_data():
    """Load raw datasets"""
    movies = pd.read_csv(RAW_DIR / "movies_raw.csv")
    sales = pd.read_csv(RAW_DIR / "daily_sales_raw.csv")
    return movies, sales

def clean_movies_data(movies_df):
    """Clean and process movies dataset"""
    
    # Convert date columns
    movies_df['release_date'] = pd.to_datetime(movies_df['release_date'])
    
    # Add derived columns
    movies_df['release_year'] = movies_df['release_date'].dt.year
    movies_df['release_month'] = movies_df['release_date'].dt.month
    movies_df['profit'] = movies_df['total_gross'] - movies_df['budget']
    movies_df['roi'] = ((movies_df['total_gross'] - movies_df['budget']) / movies_df['budget'] * 100).round(2)
    
    # Create budget categories
    movies_df['budget_category'] = pd.cut(
        movies_df['budget'], 
        bins=[0, 10_000_000, 50_000_000, 100_000_000, float('inf')],
        labels=['Low Budget', 'Medium Budget', 'High Budget', 'Blockbuster']
    )
    
    # Create performance categories based on profit
    movies_df['performance'] = pd.cut(
        movies_df['profit'],
        bins=[-float('inf'), -10_000_000, 0, 50_000_000, float('inf')],
        labels=['Major Loss', 'Loss', 'Profit', 'Major Success']
    )
    
    return movies_df

def clean_sales_data(sales_df):
    """Clean and process sales dataset"""
    
    # Convert date column
    sales_df['date'] = pd.to_datetime(sales_df['date'])
    
    # Add time-based features
    sales_df['year'] = sales_df['date'].dt.year
    sales_df['month'] = sales_df['date'].dt.month
    sales_df['day_of_week'] = sales_df['date'].dt.day_name()
    sales_df['is_weekend'] = sales_df['date'].dt.weekday >= 5
    
    return sales_df

def create_aggregated_datasets(movies_df, sales_df):
    """Create aggregated datasets for analysis"""
    
    # Monthly aggregations
    monthly_sales = sales_df.groupby(['year', 'month']).agg({
        'tickets_sold': 'sum',
        'revenue': 'sum',
        'movie_id': 'nunique'
    }).reset_index()
    monthly_sales.columns = ['year', 'month', 'total_tickets', 'total_revenue', 'unique_movies']
    
    # Genre analysis
    genre_stats = movies_df.groupby('genre').agg({
        'budget': ['mean', 'median'],
        'total_gross': ['mean', 'median', 'sum'],
        'imdb_rating': 'mean',
        'profit': ['mean', 'median'],
        'movie_id': 'count'
    }).round(2)
    genre_stats.columns = ['avg_budget', 'median_budget', 'avg_gross', 'median_gross', 
                          'total_gross', 'avg_rating', 'avg_profit', 'median_profit', 'movie_count']
    genre_stats = genre_stats.reset_index()
    
    # Studio analysis
    studio_stats = movies_df.groupby('studio').agg({
        'budget': ['mean', 'sum'],
        'total_gross': ['mean', 'sum'],
        'imdb_rating': 'mean',
        'movie_id': 'count'
    }).round(2)
    studio_stats.columns = ['avg_budget', 'total_budget', 'avg_gross', 'total_gross', 'avg_rating', 'movie_count']
    studio_stats = studio_stats.reset_index()
    
    # Top performers
    top_grossing = movies_df.nlargest(50, 'total_gross')[['title', 'genre', 'studio', 'total_gross', 'budget', 'profit', 'imdb_rating']]
    top_rated = movies_df.nlargest(50, 'imdb_rating')[['title', 'genre', 'studio', 'imdb_rating', 'total_gross', 'budget']]
    
    return {
        'monthly_sales': monthly_sales,
        'genre_stats': genre_stats,
        'studio_stats': studio_stats,
        'top_grossing': top_grossing,
        'top_rated': top_rated
    }

def main():
    """Main processing pipeline"""
    
    print("Loading raw data...")
    movies, sales = load_raw_data()
    
    print("Cleaning movies data...")
    movies_clean = clean_movies_data(movies)
    
    print("Cleaning sales data...")
    sales_clean = clean_sales_data(sales)
    
    print("Creating aggregated datasets...")
    aggregated = create_aggregated_datasets(movies_clean, sales_clean)
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    movies_clean.to_csv(PROCESSED_DIR / "movies_processed.csv", index=False)
    sales_clean.to_csv(PROCESSED_DIR / "sales_processed.csv", index=False)
    for name, df in aggregated.items():
        df.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
    
    print("\n=== Processing Complete ===")
    print(f"Processed {len(movies_clean)} movies")
    print(f"Processed {len(sales_clean)} sales records")
    print(f"Created {len(aggregated)} aggregated datasets")
    
    # Display some insights
    print("\n=== Quick Insights ===")
    print(f"Most profitable genre: {aggregated['genre_stats'].loc[aggregated['genre_stats']['avg_profit'].idxmax(), 'genre']}")
    print(f"Highest rated genre: {aggregated['genre_stats'].loc[aggregated['genre_stats']['avg_rating'].idxmax(), 'genre']}")
    print(f"Most active studio: {aggregated['studio_stats'].loc[aggregated['studio_stats']['movie_count'].idxmax(), 'studio']}")
    
    print("\nProcessed data saved to data/processed/")

if __name__ == "__main__":
    main()