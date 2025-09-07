# weather_api.py
# Utilities to fetch Open-Meteo hourly temps and persist/read from DB.

from datetime import datetime
from typing import List, Tuple, Optional

import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry

from sqlalchemy import create_engine, select, desc
from sqlalchemy.orm import sessionmaker

from models import Base, WeatherData, TrackedCity  
from config import DATABASE_URL, TRACKED_CITIES                    

# ---------- DB ----------
engine = create_engine(DATABASE_URL, future=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, future=True)

# ---------- Open-Meteo client ----------
def _get_openmeteo_client():
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)

def fetch_hourly_dataframe(latitude: float, longitude: float) -> pd.DataFrame:
    """Fetch hourly temperature_2m from Open-Meteo and return a DataFrame."""
    client = _get_openmeteo_client()
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": latitude, "longitude": longitude, "hourly": "temperature_2m"}

    responses = client.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()
    temps = hourly.Variables(0).ValuesAsNumpy()

    idx = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    )

    df = pd.DataFrame({"timestamp": idx, "temperature": temps})
    # store as naive UTC to match your models.DateTime
    df["timestamp"] = df["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None)
    return df

# ---------- DB helpers ----------
def ensure_all_cities_tracked():
    with SessionLocal() as session:
        for city in TRACKED_CITIES.keys():
            # Simple check: does city exist?
            existing = session.execute(select(TrackedCity).where(TrackedCity.city == city)).first()
            if not existing:
                session.add(TrackedCity(city=city))
        session.commit()


def upsert_city_hourly(session, city: str, df: pd.DataFrame) -> int:
    inserted = 0
    for _, row in df.iterrows():
        ts = row["timestamp"].to_pydatetime() if isinstance(row["timestamp"], pd.Timestamp) else row["timestamp"]
        exists = session.execute(
            select(WeatherData.id).where(WeatherData.city == city, WeatherData.timestamp == ts)
        ).first()
        if not exists:
            session.add(WeatherData(city=city, temperature=float(row["temperature"]), timestamp=ts))
            inserted += 1
    return inserted

def ingest_one(city: str, latitude: float, longitude: float) -> int:
    """Fetch & store hourly temps for a single city. Returns inserted row count."""
    df = fetch_hourly_dataframe(latitude, longitude)
    with SessionLocal.begin() as session:
        count = upsert_city_hourly(session, city, df)
    return count

def get_latest(city: str) -> Optional[Tuple[str, float, datetime]]:
    """Return latest (city, temperature, timestamp) or None."""
    with SessionLocal() as session:
        row = session.execute(
            select(WeatherData)
            .where(WeatherData.city == city)
            .order_by(desc(WeatherData.timestamp))
            .limit(1)
        ).scalar_one_or_none()
        if not row:
            return None
        return (row.city, row.temperature, row.timestamp)

def list_tracked_cities() -> List[str]:
    with SessionLocal() as session:
        return [c.city for c in session.execute(select(TrackedCity)).scalars().all()]
