# 🌤️ Weather Data Tracker

Automated weather data collection and visualization system with interactive dashboard.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

Collects hourly weather data from multiple cities using Open-Meteo API and displays it through a Streamlit dashboard. Features automated data collection, city management, and interactive charts.

## Features

- Automated hourly weather data collection
- Multi-city tracking with configurable coordinates  
- Interactive Streamlit dashboard
- SQLAlchemy database with migrations
- Data filtering and pagination
- Temperature trend charts

## Tech Stack

- **Backend**: Python, SQLAlchemy, Alembic
- **Frontend**: Streamlit
- **Database**: SQLite
- **API**: Open-Meteo Weather API
- **Data**: Pandas, NumPy

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database**
   ```bash
   alembic upgrade head
   ```

3. **Collect weather data**
   ```bash
   python scheduler.py
   ```

4. **Launch dashboard**
   ```bash
   streamlit run main.py
   ```

Access at `http://localhost:8501`

## Configuration

Add cities in `config.py`:

```python
TRACKED_CITIES = {
    "Berlin": {"lat": 52.52, "lon": 13.41},
    "London": {"lat": 51.5074, "lon": -0.1278},
    # Add more cities here
}
```

## License

MIT License
