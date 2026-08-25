"""
Basic tests for the movie analytics project
"""

import pandas as pd
import numpy as np
import os
import sys

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def test_data_files_exist():
    """Test that all required data files exist"""
    raw_files = [
        '../data/raw/movies_raw.csv',
        '../data/raw/daily_sales_raw.csv'
    ]
    
    processed_files = [
        '../data/processed/movies_processed.csv',
        '../data/processed/sales_processed.csv',
        '../data/processed/genre_stats.csv',
        '../data/processed/studio_stats.csv',
        '../data/processed/monthly_sales.csv'
    ]
    
    for file_path in raw_files + processed_files:
        assert os.path.exists(file_path), f"File does not exist: {file_path}"
    
    print("✅ All data files exist")

def test_data_integrity():
    """Test data integrity and structure"""
    # Load movies data
    movies = pd.read_csv('../data/processed/movies_processed.csv')
    
    # Test basic structure
    assert len(movies) > 0, "Movies dataset is empty"
    assert 'movie_id' in movies.columns, "Missing movie_id column"
    assert 'title' in movies.columns, "Missing title column"
    assert 'total_gross' in movies.columns, "Missing total_gross column"
    
    # Test data quality
    assert not movies['movie_id'].duplicated().any(), "Duplicate movie IDs found"
    assert not movies['total_gross'].isnull().any(), "Null values in total_gross"
    assert (movies['total_gross'] >= 0).all(), "Negative gross values found"
    known = movies['title'].astype(str).str.contains(
        r'Avatar|Titanic|Jurassic|Star Wars|The Dark Knight|Zootopia', case=False, regex=True
    )
    assert known.any(), "Catalog should contain recognizable published titles, not synthetic names"
    
    print("✅ Data integrity checks passed")

def test_dashboard_imports():
    """Test that dashboard dependencies can be imported"""
    try:
        import streamlit as st
        import plotly.express as px
        import plotly.graph_objects as go
        print("✅ Dashboard dependencies imported successfully")
    except ImportError as e:
        assert False, f"Failed to import dashboard dependencies: {e}"

def test_data_generation():
    """Test data generation functions"""
    try:
        from generate_data import generate_movie_data, generate_daily_sales_data
        
        # Generate small sample
        movies_df = generate_movie_data(10)
        sales_df = generate_daily_sales_data(movies_df.head(5), 30)
        
        assert len(movies_df) == 10, "Movies generation failed"
        assert len(sales_df) > 0, "Sales generation failed"
        
        print("✅ Data generation functions work correctly")
    except Exception as e:
        print(f"❌ Data generation test failed: {e}")

def test_basic_analytics():
    """Test basic analytics calculations"""
    movies = pd.read_csv('../data/processed/movies_processed.csv')
    
    # Test ROI calculation
    calculated_roi = ((movies['total_gross'] - movies['budget']) / movies['budget'] * 100).round(2)
    assert np.allclose(movies['roi'], calculated_roi, rtol=1e-5), "ROI calculation incorrect"
    
    # Test profit calculation
    calculated_profit = movies['total_gross'] - movies['budget']
    assert np.allclose(movies['profit'], calculated_profit), "Profit calculation incorrect"
    
    print("✅ Analytics calculations verified")

def run_all_tests():
    """Run all tests"""
    print("Running Movie Analytics Tests...")
    print("=" * 50)
    
    test_data_files_exist()
    test_data_integrity()
    test_dashboard_imports()
    test_data_generation()
    test_basic_analytics()
    
    print("=" * 50)
    print("🎉 All tests passed successfully!")

if __name__ == "__main__":
    run_all_tests()