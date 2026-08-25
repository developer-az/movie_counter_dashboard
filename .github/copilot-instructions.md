# Movie Industry Analytics Project

**ALWAYS follow these instructions first and only fallback to search or bash exploration when the information here is incomplete or found to be in error.**

This is a Python-based data science project that analyzes movie industry trends through synthetic data generation, processing, analysis, and interactive visualization using Streamlit.

## Working Effectively

### Bootstrap and Setup (4-5 minutes total)
Run these commands in exact sequence:

```bash
# Install Python dependencies (takes ~3 minutes, NEVER CANCEL)
pip install --break-system-packages -r requirements.txt
```

```bash
# Generate and process sample data (takes ~15 seconds total)
cd scripts
python3 generate_data.py
python3 data_processing.py  
cd ..
```

```bash
# Validate installation (takes ~5 seconds)
cd tests
python3 test_basic.py
cd ..
```

### Run the Application (15 seconds startup)
```bash
# Start the dashboard (takes ~15 seconds to initialize, NEVER CANCEL)
streamlit run dashboard/streamlit_app.py --server.port 8501
```

Access the application at `http://localhost:8501`

### Validate Application Works
```bash
# Test dashboard accessibility 
curl -s -I http://localhost:8501 | head -1
# Should return: HTTP/1.1 200 OK
```

## Validation Scenarios

**ALWAYS run through these complete scenarios after making changes:**

### Complete End-to-End Workflow
1. **Data Pipeline Test**:
   ```bash
   cd scripts
   python3 generate_data.py    # Should generate 500 movies, ~7K sales records
   python3 data_processing.py  # Should process all data successfully
   cd ..
   ```

2. **System Validation**:
   ```bash
   cd tests  
   python3 test_basic.py       # Should show "All tests passed successfully!"
   cd ..
   ```

3. **Dashboard Functionality**:
   ```bash
   streamlit run dashboard/streamlit_app.py --server.port 8501 --server.headless true &
   sleep 20  # Wait for startup
   curl -s -I http://localhost:8501 | head -1  # Should return HTTP/1.1 200 OK
   pkill -f streamlit
   ```

### Manual Testing Scenarios
**CRITICAL**: After code changes, ALWAYS manually verify:

1. **Dashboard Loads**: Navigate to `http://localhost:8501` and verify the page loads without errors
2. **Data Displays**: Check that all 6 views (Overview, Genres, Studios, Trends, Sales, Explorer) show data
3. **Interactivity Works**: Switch views (only one renders), then change filters and confirm charts and KPIs update
4. **No Errors**: Check browser console and terminal for any error messages

## Build and Test Commands

### Development Workflow
```bash
# Quick validation (30 seconds total)
cd tests && python3 test_basic.py && cd ..
streamlit run dashboard/streamlit_app.py --server.port 8501 --server.headless true &
sleep 15
curl -s -I http://localhost:8501 | head -1  # Should return HTTP/1.1 200 OK
pkill -f streamlit
```

### Dependency Management
```bash
# Check Python environment
python3 --version  # Should be 3.8+

# Verify all dependencies installed
python3 -c "import streamlit, pandas, plotly; print('All core dependencies available')"

# Check data files exist
ls -la data/processed/ | grep -E "(movies|sales|genre|studio|monthly).*\.csv" | wc -l  # Should show 5
```

## Time Expectations and Timeouts

**CRITICAL TIMING INFO - NEVER CANCEL THESE OPERATIONS:**

- **Dependency Installation**: Takes 2-4 minutes (use 300+ second timeout)
- **Data Generation**: Takes 5-15 seconds (use 60+ second timeout)
- **Data Processing**: Takes 5-15 seconds (use 60+ second timeout)
- **Dashboard Startup**: Takes 10-20 seconds (use 60+ second timeout)
- **Tests**: Takes 3-10 seconds (use 30+ second timeout)

## Project Structure and Key Locations

### Core Components
```
movie_counter_project/
├── scripts/                   # Data pipeline
│   ├── generate_data.py      # Creates 500 movies + sales data
│   └── data_processing.py    # Cleans and processes data
├── dashboard/
│   └── streamlit_app.py      # Main application (5 interactive tabs)
├── tests/
│   └── test_basic.py         # Validates all components work
├── data/
│   ├── raw/                  # Generated datasets
│   └── processed/            # Clean analysis-ready data
└── requirements.txt          # Python dependencies
```

### Important Files to Check When Making Changes
- **Dashboard code**: `dashboard/streamlit_app.py` (main application)
- **Data pipeline**: `scripts/generate_data.py` and `scripts/data_processing.py`
- **Tests**: `tests/test_basic.py` (validates everything works)
- **Configuration**: `requirements.txt` (dependencies)

## Common Issues and Solutions

### Externally Managed Environment Error
```bash
# Use system package override
pip install --break-system-packages -r requirements.txt
```

### Python Command Not Found
```bash
# Always use python3 (not python)
python3 generate_data.py
python3 data_processing.py
```

### Port Already in Use
```bash
# Kill existing streamlit process
pkill -f streamlit
# Or use different port
streamlit run dashboard/streamlit_app.py --server.port 8502
```

### Data Files Missing
```bash
# Regenerate all data
cd scripts
python3 generate_data.py && python3 data_processing.py
cd ..
```

## Development Best Practices

### Before Making Changes
1. **Always run tests first**: `cd tests && python3 test_basic.py && cd ..`
2. **Check current data**: Ensure `data/processed/` contains 5 CSV files
3. **Verify dashboard works**: Test that application starts and loads data

### After Making Changes  
1. **Re-run data pipeline**: If you modified data generation or processing
2. **Run tests**: `cd tests && python3 test_basic.py && cd ..`
3. **Test dashboard**: Start app and manually verify functionality
4. **Check syntax**: `python3 -m py_compile dashboard/streamlit_app.py`

### Code Quality Checks
```bash
# Validate Python syntax
find . -name "*.py" -exec python3 -m py_compile {} \;

# Check imports work
python3 -c "from scripts import generate_data, data_processing"
```

## Application Features

The dashboard provides 6 main views (only the active view is rendered):

1. **Overview**: KPI deltas, budget vs box office (WebGL), ROI distribution, lead titles
2. **Genres**: Treemap, ROI spread, live genre ledger
3. **Studios**: Rankings, volume vs yield, live studio ledger
4. **Trends**: Release and revenue by year
5. **Sales**: Auto-rolled time series, weekend effect (scoped to filtered titles)
6. **Explorer**: Sortable table + CSV export

### Sample Data Characteristics
- **500 movies** across 10 genres (Action, Comedy, Drama, etc.)
- **~7,000 daily sales records** covering 365 days
- **Multiple studios** with realistic budget/revenue distributions
- **IMDb ratings** from 1-10 with genre-based variations
- **Financial metrics** including ROI, profit calculations

## Quick Reference Commands

```bash
# Full setup from scratch
pip install --break-system-packages -r requirements.txt
cd scripts && python3 generate_data.py && python3 data_processing.py && cd ..
cd tests && python3 test_basic.py && cd ..

# Start development
streamlit run dashboard/streamlit_app.py --server.port 8501

# Quick validation  
curl -s -I http://localhost:8501 | head -1

# Reset data
cd scripts && python3 generate_data.py && python3 data_processing.py && cd ..
```

---

**Remember**: This is a data analytics application, not a user authentication system. Focus testing on data loading, visualization, and interactive features rather than login flows.