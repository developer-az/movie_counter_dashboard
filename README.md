# Movie Industry Analytics Project

A comprehensive data science project analyzing movie industry trends, box office performance, and consumer behavior through interactive visualizations and statistical analysis.

## 🎯 Project Overview

This project transforms movie industry data into actionable insights through advanced analytics and multiple interfaces. It demonstrates proficiency in data collection, processing, analysis, and visualization using modern data science tools and techniques, with **enhanced scalability** and **reduced dependency** on any single interface.

### Key Objectives
- **Multi-Interface Architecture**: Dashboard, terminal, and programmatic access
- **Data Analysis**: Comprehensive exploration of movie industry trends and patterns
- **Scalable Design**: Modular architecture supporting future growth
- **Insights Generation**: Extract actionable business intelligence from raw data
- **Technical Excellence**: Showcase best practices in data science workflow

## 📊 Features

### Multiple Interfaces
- **🖥️ Interactive Dashboard**: Streamlit-powered web interface with real-time filtering
- **💻 Terminal Interface**: Command-line analytics for automation and quick insights  
- **📄 Export Capabilities**: JSON, CSV outputs for integration with other tools
- **⚡ Programmatic Access**: Shared analytics core for custom applications

### Data Analytics
- **3,400+ published titles**: The Numbers box office extract plus household-name fills, with budget, revenue, ratings, and metadata
- **Time Series Analysis**: Daily sales tracking and seasonal patterns
- **Genre & Studio Analysis**: Performance metrics across categories
- **ROI Calculations**: Financial performance and profitability analysis

### Interactive Dashboard
- **Original analysis tabs**: Overview, Genre Analysis, Studio Performance, Trends, Sales Data, plus a searchable Catalog
- **Recognizable films**: Published box office (The Numbers) plus household-name fills (Avatar, Titanic, The Dark Knight, Endgame, …)
- **Filters**: Title search, release window, genre, optional studio, budget range
- **Useful chart overlays**: Break-even line, 0% ROI marker, log-scale scatter, live tables from the filtered slice

### Technical Features
- **Automated Data Pipeline**: Scripts for data generation and processing
- **Jupyter Notebooks**: Detailed exploratory data analysis
- **Clean Architecture**: Well-organized codebase with separation of concerns
- **Documentation**: Comprehensive project documentation and code comments

## 🏗️ Project Structure

```
movie_counter_project/
├── analytics/                  # 🆕 Shared analytics core
│   ├── __init__.py
│   └── core.py                # Reusable analytics functions
├── data/                      # Data storage
│   ├── raw/                   # Raw datasets
│   │   ├── movie_profit.csv           # The Numbers / TidyTuesday extract
│   │   ├── imdb_movie_metadata.csv    # Public IMDb scores + runtimes
│   │   ├── movies_raw.csv
│   │   └── daily_sales_raw.csv
│   └── processed/             # Cleaned and processed data
│       ├── movies_processed.csv
│       ├── sales_processed.csv
│       ├── genre_stats.csv
│       ├── studio_stats.csv
│       └── monthly_sales.csv
├── notebooks/                 # Jupyter notebooks for analysis
│   └── movie_eda.ipynb       # Exploratory Data Analysis
├── scripts/                   # Data processing scripts
│   ├── generate_data.py      # Synthetic data generation
│   ├── data_processing.py    # Data cleaning and transformation
│   ├── database_operations.py # Database operations (terminal interface)
│   └── create_table.sql      # Database schema
├── dashboard/                 # Interactive web dashboard
│   └── streamlit_app.py      # Main dashboard application
├── docs/                      # Documentation
│   ├── technical_documentation.md
│   └── scalability_analysis.md # 🆕 Scalability assessment
├── tests/                     # Unit tests
├── movie_analytics_terminal.py # 🆕 Command-line interface
├── .github/workflows/         # CI/CD workflows (placeholder)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── LICENSE                    # MIT License
```

## 🚀 Quick Start

### ⚡ Quick Setup Checklist
- [ ] Install system dependencies (`python3-full`, `python3-venv`)
- [ ] Install Python packages (`pip install --break-system-packages -r requirements.txt`)
- [ ] Generate data (`python3 scripts/generate_data.py`)
- [ ] Process data (`python3 scripts/data_processing.py`)
- [ ] Run tests (`python3 tests/test_basic.py`)
- [ ] **🆕 Terminal interface**: `python3 movie_analytics_terminal.py`
- [ ] **OR Dashboard**: `streamlit run dashboard/streamlit_app.py --server.port 8501`
- [ ] Access dashboard at `http://localhost:8501`

### Prerequisites
- **Python 3.8+**: Required for all dependencies
- **pip**: Python package manager
- **python3-venv** (recommended): For virtual environment management
- **python3-full**: Complete Python installation with all components

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/developer-az/movie_counter_project.git
   cd movie_counter_project
   ```

2. **Install system dependencies** (Ubuntu/Debian):
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv python3-full
   ```

3. **Install Python dependencies**:
   
   **Option A: Using system packages (if you encounter externally-managed-environment error)**:
   ```bash
   pip install --break-system-packages -r requirements.txt
   ```
   
   **Option B: Using virtual environment (recommended)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Generate sample data**:
   ```bash
   cd scripts
   python3 generate_data.py
   python3 data_processing.py
   cd ..
   ```

5. **Test the setup**:
   ```bash
   cd tests
   python3 test_basic.py
   cd ..
   ```

6. **Launch the interface of your choice**:

   **Option A: Terminal Interface (New!)**
   ```bash
   # Interactive mode
   python3 movie_analytics_terminal.py
   
   # Quick overview
   python3 movie_analytics_terminal.py --overview
   
   # Export report
   python3 movie_analytics_terminal.py --export json
   ```

   **Option B: Web Dashboard**
   ```bash
   cd dashboard
   streamlit run streamlit_app.py --server.port 8501
   ```

7. **For dashboard**: Open your browser to `http://localhost:8501`

### Alternative: Jupyter Analysis
To explore the data analysis notebooks:
```bash
jupyter notebook notebooks/movie_eda.ipynb
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### **1. Externally Managed Environment Error**
**Error**: `error: externally-managed-environment`

**Solution**: Use one of these approaches:
```bash
# Option 1: Install with system override
pip install --break-system-packages -r requirements.txt

# Option 2: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **2. Python Command Not Found**
**Error**: `Command 'python' not found, did you mean: command 'python3'`

**Solution**: Use `python3` instead of `python`:
```bash
python3 generate_data.py
python3 data_processing.py
```

#### **3. Dashboard Syntax Errors**
**Error**: `SyntaxError: unexpected character after line continuation character`

**Solution**: The dashboard file has been fixed. If you encounter this:
1. Ensure you have the latest version of `dashboard/streamlit_app.py`
2. Check for any malformed string literals
3. Run: `python3 -m py_compile dashboard/streamlit_app.py`

#### **4. Data Files Not Found**
**Error**: `FileNotFoundError: [Errno 2] No such file or directory`

**Solution**: Ensure data generation completed successfully:
```bash
cd scripts
python3 generate_data.py
python3 data_processing.py
cd ..
ls -la data/processed/  # Should show CSV files
```

#### **5. Port Already in Use**
**Error**: `Port 8501 is already in use`

**Solution**: Use a different port or kill existing process:
```bash
# Kill existing streamlit process
pkill -f streamlit

# Or use different port
streamlit run streamlit_app.py --server.port 8502
```

#### **6. Virtual Environment Issues**
**Error**: `bash: venv/bin/activate: No such file or directory`

**Solution**: Recreate the virtual environment:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ⚖️ Scalability and Architecture

### Current Architecture Assessment ⭐⭐⭐⭐ (4/5 Stars)

**Strengths**:
- ✅ **Modular design** with shared analytics core
- ✅ **Multiple interfaces** reduce single points of failure  
- ✅ **Clean separation** of data, processing, and presentation layers
- ✅ **Export capabilities** for integration with other systems

**Suitable for**:
- 📊 Small to medium datasets (up to ~100K records)
- 👥 Teams requiring both dashboard and programmatic access
- 🔄 Development and prototyping workflows
- 📈 Business intelligence and reporting use cases

### Scaling Path

| **Stage** | **Data Size** | **Users** | **Recommended Setup** |
|-----------|---------------|-----------|----------------------|
| **Development** | <1K records | 1-5 | Local files + terminal interface |
| **Small Production** | 1K-10K | 5-50 | CSV files + Streamlit Cloud |  
| **Medium Production** | 10K-100K | 50-500 | Database + containerization |
| **Large Scale** | 100K+ | 500+ | Data warehouse + microservices |

### Future Enhancements

**Phase 1** (Enhanced Scalability):
- Database integration (PostgreSQL)
- RESTful API layer
- Docker containerization

**Phase 2** (Production Features):
- Real-time data ingestion
- User authentication
- Advanced ML analytics

**Phase 3** (Enterprise Scale):
- Microservices architecture
- Cloud-native deployment
- Data warehouse integration

**For detailed scalability analysis**, see [`docs/scalability_analysis.md`](docs/scalability_analysis.md)

### Verification Steps

After installation, verify everything works:

1. **Check Python version**:
   ```bash
   python3 --version  # Should be 3.8+
   ```

2. **Verify dependencies**:
   ```bash
   python3 -c "import streamlit, pandas, plotly; print('All dependencies installed!')"
   ```

3. **Test data generation**:
   ```bash
   cd tests
   python3 test_basic.py
   ```

4. **Check dashboard syntax**:
   ```bash
   python3 -m py_compile dashboard/streamlit_app.py
   ```

5. **Verify dashboard access**:
   ```bash
   curl -s -I http://localhost:8501 | head -1
   # Should return: HTTP/1.1 200 OK
   ```

## 📈 Dashboard Features

The dashboard is a single-page workspace (`dashboard/streamlit_app.py`) with the original five analysis tabs plus a searchable catalog. Sidebar filters apply to every tab.

### Overview
- **KPI row**: Titles, worldwide box office, average IMDb, profitable share, **median ROI**
- **Budget vs box office** (log scale) with a break-even line
- **ROI distribution** with 0% and median markers
- **Top 10** by worldwide gross and by ROI

### Genre Analysis
- **Pie chart** of title counts by genre
- **Average box office** by genre
- **ROI spread** (box plot) plus a detailed genre table computed from the current filters

### Studio Performance
- Ranked box office bars (top 15)
- Volume vs average yield scatter
- Studio statistics table

### Trends
- Titles and average box office by year
- IMDb vs year, sized by budget

### Sales Data
- Daily tickets and revenue, weekend vs weekday, top 15 by tickets
- Built from an 8-week theatrical model scaled to each film's **reported domestic gross** (top 100 domestic titles)

### Catalog
- Sortable table of the filtered slice and CSV download

## 💻 Terminal Interface Features (New!)

### Interactive Mode
```bash
python3 movie_analytics_terminal.py
```
- Menu-driven interface with numbered options
- Real-time data exploration
- Export capabilities built-in

### Command-Line Mode
```bash
# Quick insights
python3 movie_analytics_terminal.py --overview
python3 movie_analytics_terminal.py --genre --studio

# Top performers
python3 movie_analytics_terminal.py --top revenue 10
python3 movie_analytics_terminal.py --top rating 5

# Full analysis
python3 movie_analytics_terminal.py --full-report

# Export reports
python3 movie_analytics_terminal.py --export json --output report.json
python3 movie_analytics_terminal.py --export csv --output metrics.csv
```

### Benefits of Terminal Interface
- 🚀 **Faster startup** (~500ms vs 2-3s for dashboard)
- 🤖 **Automation-friendly** with command-line arguments
- 📊 **Same insights** as dashboard in text format
- 💾 **Export capabilities** for integration with other tools
- 🌐 **No web dependencies** for server environments

## 🔍 Data Insights

### Key Findings
Figures below are from the published catalog (The Numbers extract plus household-name fills), not the old synthetic titles.

- **Adventure** leads total and average profitability in this slice
- **Drama** has the highest average IMDb score
- **Warner Bros** is the most active studio by title count
- Modeled weekend ticket demand is about **55%** above weekdays (Friday/weekend weights in the theatrical curve)
- About **68%** of titles recoup their production budget at the worldwide box office
- **Median ROI** is the headline profitability KPI; the mean is pulled up by a few micro-budget breakouts

### Business Intelligence
- Budget allocation strategies by genre performance
- Seasonal release timing optimization
- Studio partnership and investment decisions
- Market trend identification and forecasting

## 🛠️ Technical Stack

### Core Technologies
- **Python 3.8+**: Primary programming language
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Streamlit**: Interactive web dashboard framework

### Visualization Libraries
- **Plotly**: Interactive charts and graphs
- **Matplotlib**: Statistical plotting
- **Seaborn**: Statistical data visualization
- **Altair**: Declarative statistical visualization

### Data Science Tools
- **Jupyter**: Interactive development environment
- **Scikit-learn**: Machine learning library
- **psycopg2**: PostgreSQL database connectivity

## 📊 Data Schema

### Movies Dataset
- **movie_id**: Unique identifier
- **title**: Movie title
- **genre**: Movie category
- **release_date**: Release date
- **rating**: MPAA rating (G, PG, PG-13, R, NC-17)
- **studio**: Production studio
- **runtime_minutes**: Movie duration
- **budget**: Production budget
- **domestic_gross**: US box office revenue
- **international_gross**: International revenue
- **total_gross**: Combined revenue
- **imdb_rating**: IMDb score (1-10)
- **roi**: Return on investment percentage
- **profit**: Net profit (revenue - budget)

### Sales Dataset
- **movie_id**: Reference to movies table
- **movie_title**: Movie name
- **date**: Sale date
- **tickets_sold**: Number of tickets
- **revenue**: Daily revenue

## 🧪 Development

### Data Generation
The catalog is built from published financials (`scripts/generate_data.py`):
- **The Numbers** extract (TidyTuesday `movie_profit.csv`) for budget, domestic/worldwide gross, studio, MPAA, genre, and release date
- **IMDb 5000** public extract for scores and runtimes, plus published scores for titles that extract misses
- **Household-name fills** (Avatar, Titanic, The Dark Knight, Endgame, …) when the extract omits a widely reported film
- **Theatrical ticket model**: 8-week decay curve for the 100 highest domestic-gross titles, scaled so each run sums to reported domestic gross

### Recent Fixes and Improvements

#### **Dashboard Syntax Issues (Fixed)**
- **Problem**: Malformed string literals in `dashboard/streamlit_app.py` caused syntax errors
- **Solution**: Completely rewrote the dashboard file with proper Python syntax
- **Status**: ✅ **RESOLVED**

#### **Python Environment Issues (Addressed)**
- **Problem**: Ubuntu's externally-managed-environment prevented pip installations
- **Solution**: Added `--break-system-packages` flag and virtual environment options
- **Status**: ✅ **RESOLVED**

#### **Command Compatibility (Fixed)**
- **Problem**: `python` command not available, only `python3`
- **Solution**: Updated all documentation to use `python3` explicitly
- **Status**: ✅ **RESOLVED**

### Testing
Run tests to validate data processing:
```bash
cd tests
python -m pytest
```

### Code Quality
- **PEP 8**: Python style guide compliance
- **Documentation**: Comprehensive docstrings and comments
- **Error Handling**: Robust exception management
- **Performance**: Optimized data processing with caching

## 📈 Future Enhancements

### Planned Features
- **Machine Learning**: Predictive models for box office success
- **Real-time Data**: Integration with live movie APIs
- **Advanced Analytics**: Sentiment analysis, market segmentation
- **Mobile Optimization**: Responsive dashboard design

### Technical Improvements
- **Database Integration**: PostgreSQL backend implementation
- **API Development**: RESTful API for data access
- **Docker Deployment**: Containerized application
- **Cloud Deployment**: AWS/Azure hosting options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

**Developer**: developer-az
**Project**: Movie Industry Analytics
**Repository**: https://github.com/developer-az/movie_counter_project

---

*Built with ❤️ using Python, Streamlit, and modern data science tools*